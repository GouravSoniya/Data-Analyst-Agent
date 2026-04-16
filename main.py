import os
from typing import Literal
from pydantic import BaseModel
from openai import OpenAI
from executor import execute_python_code

MAX_STEPS = 10
MAX_HISTORY_MESSAGES = 20

GROQ_MODEL = "llama-3.3-70b-versatile"


def setup_provider() -> tuple[OpenAI, str]:
    """Ask the user which backend to use and return (client, model_name)."""

    print("Select backend:")
    print("  [1] LM Studio  (local, no internet needed)")
    print("  [2] Groq        (free API, needs internet)")

    while True:
        choice = input("\nEnter 1 or 2: ").strip()
        if choice in ("1", "2"):
            break
        print("Invalid choice. Enter 1 or 2.")

    if choice == "1":
        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        model = "local-model"
        print("\n✅ Using LM Studio at localhost:1234\n")
        return client, model

    # --- Groq setup ---
    print("\nGet your free API key at: https://console.groq.com/keys")
    while True:
        api_key = input("Enter your Groq API key: ").strip()
        if api_key:
            break
        print("API key cannot be empty.")

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )
    print(f"\n✅ Using Groq with {GROQ_MODEL}\n")
    return client, GROQ_MODEL


class AgentResponse(BaseModel):
    thought: str
    action: Literal["message", "code"]
    output: str


def load_csv_preview(file_path: str, code_namespace: dict):
    code = f"""
import pandas as pd
df = pd.read_csv(r"{file_path}")
print(df.head(3))
    """
    result = execute_python_code(code, code_namespace)

    if "Traceback" in result:
        return None, result

    return result, None


def trim_history(history):
    system = history[:1]
    rest = history[1:]
    return system + rest[-MAX_HISTORY_MESSAGES:]


def build_system_prompt(csv_preview=None, file_path=None):
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
        "  WRONG: \"output\": \"Calculating the average...\"\n"
        "  WRONG: \"output\": \"```python\\nprint(df.head())\\n```\"\n"
        "  RIGHT: \"output\": \"print(df.groupby('gender')['age'].mean())\"\n"
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
        "- Do NOT repeat the same computation\n"
        f"{'CSV Preview:\n' + csv_preview if csv_preview else ''}"
    )


def result_looks_like_prose(text: str) -> bool:
    """Returns True if the output field looks like natural language instead of Python code."""
    text = text.strip()
    python_indicators = ["print(", "df", "import ", "=", "(", ")", "#", "for ", "if "]
    has_python = any(indicator in text for indicator in python_indicators)
    return not has_python


def main():
    print("--- Data Analyst Agent ---\n")

    client, model = setup_provider()

    while True:
        path = input("CSV path: ").strip()
        if os.path.exists(path):
            break
        print("Invalid path.\n")

    namespace = {}
    preview, err = load_csv_preview(path, namespace)

    if err:
        print(f"Failed to load CSV:\n{err}")
        return

    print(preview)

    history = [{
        "role": "system",
        "content": build_system_prompt(preview, path)
    }]

    while True:
        user = input("\nYou: ").strip()

        if user in ["exit", "quit"]:
            break

        history.append({"role": "user", "content": user})
        history = trim_history(history)

        steps = 0

        while steps < MAX_STEPS:
            steps += 1
            print(f"\n[Step {steps}]")
            print("\nAgent is thinking...")

            res = client.chat.completions.create(
                model=model,
                messages=history,
                temperature=0.3,
                response_format={
                    "type": "json_object",
                }
            )

            raw = res.choices[0].message.content

            try:
                parsed = AgentResponse.model_validate_json(raw)
            except Exception:
                print("⚠️  JSON error, retrying...")
                history.append({"role": "assistant", "content": raw})
                history.append({
                    "role": "user",
                    "content": "Return valid JSON only."
                })
                continue

            print("Thought:", parsed.thought)

            if parsed.action == "code":
                history.append({"role": "assistant", "content": raw})

                if result_looks_like_prose(parsed.output):
                    print("⚠️  Output field contains prose, not code. Retrying...")
                    history.append({
                        "role": "user",
                        "content": (
                            "Your 'output' field contained plain text, not Python code. "
                            "When action is 'code', the 'output' field MUST be raw executable Python only. "
                            "No explanations, no markdown. Just the Python code itself."
                        )
                    })
                    continue

                print("\n--- CODE ---")
                print(parsed.output.strip())
                print("------------")

                print("\n--- OUTPUT ---")
                result = execute_python_code(parsed.output, namespace)
                print(result if result.strip() else "[No output]")
                print("--------------")

                if result.startswith("[BLOCKED]"):
                    print("⚠️  Execution error, asking model to fix...")
                    history.append({
                        "role": "user",
                        "content": (
                            f"Your code failed to execute with this error:\n{result}\n"
                            "Fix the Python code and try again. Return ONLY valid Python in the 'output' field."
                        )
                    })
                    continue

                history.append({
                    "role": "user",
                    "content": f"The above code was executed and produced the following output:\n{result}"
                })

            else:
                print("\nAssistant:", parsed.output)
                history.append({"role": "assistant", "content": raw})
                break

        else:
            print("\n⚠️  Max steps reached without a final answer. Try rephrasing your question.")


if __name__ == "__main__":
    main()