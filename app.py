import re
import streamlit as st
import pandas as pd
import tempfile
import os
from typing import Literal
from pydantic import BaseModel
from openai import OpenAI
from executor import execute_python_code

# ── Constants ────────────────────────────────────────────────────────────────
MAX_STEPS = 10
MAX_HISTORY_MESSAGES = 20
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Pydantic model (same as main.py) ─────────────────────────────────────────
class AgentResponse(BaseModel):
    thought: str
    action: Literal["message", "code"]
    output: str


# ── Streaming helpers ─────────────────────────────────────────────────────────
def _extract_partial_thought(text: str) -> str | None:
    """Pull the thought value out of a partially-streamed JSON string."""
    match = re.search(r'"thought"\s*:\s*"([^"]*)', text)
    return match.group(1) if match else None


def stream_llm(client: OpenAI, model: str, history: list) -> str:
    """
    Stream the LLM response token-by-token.
    While streaming, show the thought field as it types.
    Returns the full raw response string once done.
    """
    placeholder = st.empty()
    full_text = ""

    with client.chat.completions.create(
        model=model,
        messages=history,
        temperature=0.3,
        response_format={"type": "json_object"},
        stream=True,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_text += delta

            thought = _extract_partial_thought(full_text)
            if thought:
                placeholder.markdown(f"💭 *{thought}*▌")
            else:
                placeholder.markdown("⏳ *Thinking…*")

    placeholder.empty()
    return full_text


# ── Helpers (same logic as main.py) ──────────────────────────────────────────
def result_looks_like_prose(text: str) -> bool:
    text = text.strip()
    python_indicators = ["print(", "df", "import ", "=", "(", ")", "#", "for ", "if "]
    return not any(ind in text for ind in python_indicators)


def trim_history(history):
    system = history[:1]
    rest = history[1:]
    return system + rest[-MAX_HISTORY_MESSAGES:]


def build_system_prompt(csv_preview: str) -> str:
    return (
        "You are a powerful Python data analyst agent running INSIDE a live Python environment.\n\n"
        "IMPORTANT:\n"
        "- You ALREADY have access to the data via a pandas DataFrame called `df`\n"
        "- The CSV is already loaded — DO NOT say you can't access data\n"
        "- DO NOT mention SQL, databases, or limitations\n"
        "- You CAN execute Python code via the 'code' action\n\n"
        "RULES:\n"
        "1. If the user asks for ANY calculation or data analysis -> ALWAYS use action = 'code'\n"
        "2. NEVER explain how to do it - just DO it using Python\n"
        "3. NEVER return code in 'message'\n"
        "4. ALWAYS use print() to show results\n\n"
        "CRITICAL - OUTPUT FIELD RULES:\n"
        "- When action = 'code': the 'output' field MUST contain ONLY raw executable Python code.\n"
        "  NO prose, NO explanations, NO markdown, NO backticks. Just Python.\n"
        "- When action = 'message': the 'output' field contains your plain text reply to the user.\n\n"
        "OUTPUT FORMAT (respond in JSON):\n"
        "{\n"
        '  "thought": "brief reasoning",\n'
        '  "action": "code" or "message",\n'
        '  "output": "raw Python code if action=code, plain text if action=message"\n'
        "}\n\n"
        "FINAL STEP RULE:\n"
        "- After you get the final answer from code execution, you MUST respond with action = 'message'\n"
        "- Do NOT run more code after the answer is found\n"
        f"CSV Preview:\n{csv_preview}"
    )


def load_csv(file) -> tuple[pd.DataFrame | None, str | None, str | None]:
    """Load uploaded CSV, return (df, preview_str, error)."""
    try:
        df = pd.read_csv(file)
        preview = df.head(3).to_string()
        return df, preview, None
    except Exception as e:
        return None, None, str(e)


def load_api_key() -> str | None:
    """Load Groq key — st.secrets when deployed, .env when local."""
    try:
        return st.secrets["GROQ_API_KEY"]       # Streamlit Cloud
    except Exception:
        pass
    from dotenv import load_dotenv
    # Explicit path — always loads the .env next to app.py
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("GROQ_API_KEY")


def make_client():
    api_key = load_api_key()
    if not api_key:
        return None, "GROQ_API_KEY not found in .env or Streamlit secrets."
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key.strip())
    return client, GROQ_MODEL


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "client": None,
        "model": None,
        "namespace": {},
        "history": [],
        "chat_messages": [],
        "csv_loaded": False,
        "csv_preview": "",
        "key_error": None,
        "pending_input": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Auto-connect once on first load
    if st.session_state.client is None and st.session_state.key_error is None:
        client, model_or_err = make_client()
        if client is None:
            st.session_state.key_error = model_or_err
        else:
            st.session_state.client = client
            st.session_state.model = model_or_err


# ── Agent step loop ───────────────────────────────────────────────────────────
def run_agent(user_input: str):
    """Run the full multi-step agent loop for one user message."""
    client: OpenAI = st.session_state.client
    model: str = st.session_state.model
    history: list = st.session_state.history
    namespace: dict = st.session_state.namespace

    history.append({"role": "user", "content": user_input})
    history = trim_history(history)

    steps = 0
    while steps < MAX_STEPS:
        steps += 1

        raw = stream_llm(client, model, history)

        try:
            parsed = AgentResponse.model_validate_json(raw)
        except Exception:
            history.append({"role": "assistant", "content": raw})
            history.append({"role": "user", "content": "Return valid JSON only."})
            continue

        # ── CODE branch ──
        if parsed.action == "code":
            history.append({"role": "assistant", "content": raw})

            if result_looks_like_prose(parsed.output):
                history.append({
                    "role": "user",
                    "content": (
                        "Your 'output' field contained plain text, not Python code. "
                        "When action is 'code', the 'output' field MUST be raw executable Python only."
                    ),
                })
                continue

            # Add thought + code + output to display
            st.session_state.chat_messages.append({
                "role": "agent_step",
                "thought": parsed.thought,
                "code": parsed.output.strip(),
                "exec_output": None,   # filled after execution
            })

            exec_result = execute_python_code(parsed.output, namespace)
            exec_result_str = exec_result.strip() if exec_result.strip() else "[No output]"

            # Patch the last agent_step with the real output
            st.session_state.chat_messages[-1]["exec_output"] = exec_result_str

            if exec_result.startswith("[BLOCKED]"):
                history.append({
                    "role": "user",
                    "content": (
                        f"Your code failed:\n{exec_result}\n"
                        "Fix the Python code and try again. Return ONLY valid Python in the 'output' field."
                    ),
                })
                continue

            history.append({
                "role": "user",
                "content": f"Code was executed and produced:\n{exec_result}",
            })

        # ── MESSAGE branch ──
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "thought": parsed.thought,
                "content": parsed.output,
            })
            history.append({"role": "assistant", "content": raw})
            break

    else:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "thought": "",
            "content": "⚠️ Max steps reached without a final answer. Try rephrasing your question.",
        })

    st.session_state.history = history


# ── Render chat history ───────────────────────────────────────────────────────
def render_chat():
    for msg in st.session_state.chat_messages:
        role = msg["role"]

        if role == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])

        elif role == "assistant":
            with st.chat_message("assistant"):
                if msg.get("thought"):
                    with st.expander("💭 Thought", expanded=False):
                        st.caption(msg["thought"])
                st.markdown(msg["content"])

        elif role == "agent_step":
            with st.chat_message("assistant"):
                if msg.get("thought"):
                    with st.expander("💭 Thought", expanded=False):
                        st.caption(msg["thought"])
                with st.expander("🐍 Code executed", expanded=True):
                    st.code(msg["code"], language="python")
                if msg.get("exec_output"):
                    with st.expander("📤 Output", expanded=True):
                        st.text(msg["exec_output"])


# ── Main app ──────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Data Analyst Agent",
        page_icon="📊",
        layout="wide",
    )
    init_state()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("📊 Data Analyst Agent")
        st.divider()

        # CSV upload
        st.subheader("📁 Upload CSV")
        uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

        if uploaded:
            if st.button("Load CSV", use_container_width=True):
                df, preview, err = load_csv(uploaded)
                if err:
                    st.error(f"Failed to load CSV: {err}")
                else:
                    st.session_state.namespace = {"df": df}
                    st.session_state.history = [{
                        "role": "system",
                        "content": build_system_prompt(preview),
                    }]
                    st.session_state.chat_messages = []
                    st.session_state.csv_preview = preview
                    st.session_state.csv_loaded = True
                    st.success(f"Loaded {len(df)} rows × {len(df.columns)} columns")

        if st.session_state.csv_loaded:
            st.divider()
            st.subheader("🔍 Data Preview")
            st.dataframe(
                st.session_state.namespace["df"].head(5),
                use_container_width=True,
            )

        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            if st.session_state.csv_loaded:
                st.session_state.history = [{
                    "role": "system",
                    "content": build_system_prompt(st.session_state.csv_preview),
                }]

    # ── Main panel ────────────────────────────────────────────────────────────
    if st.session_state.key_error:
        st.error(f"⚠️ {st.session_state.key_error}")
        st.code("GROQ_API_KEY=gsk_your_key_here", language="bash")
        st.caption("Add this to your `.env` file and restart.")
        return

    if not st.session_state.csv_loaded:
        st.info("👈 Upload and load a CSV file in the sidebar.")
        return

    render_chat()

    user_input = st.chat_input("Ask anything about your data…")
    if user_input:
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
        })
        st.session_state.pending_input = user_input
        st.rerun()  # rerun #1 — renders user message immediately

    if st.session_state.pending_input:
        run_agent(st.session_state.pending_input)
        st.session_state.pending_input = None
        st.rerun()  # rerun #2 — renders agent response


if __name__ == "__main__":
    main()