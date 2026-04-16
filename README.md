# 🤖 Data Analyst Agent

A CLI agent that loads any CSV file and lets you query it in plain English. It writes and executes Python code under the hood to give you accurate, real answers — not hallucinated ones.

Supports two backends: **LM Studio** (fully local, no internet) and **Groq** (free cloud API).

---

## Demo

```
--- Data Analyst Agent ---

Select backend:
  [1] LM Studio  (local, no internet needed)
  [2] Groq        (free API, needs internet)

Enter 1 or 2: 2
Enter your Groq API key: gsk_...

✅ Using Groq with llama-3.3-70b-versatile

CSV path: Finance_data.csv

You: what is the average age of men and women?

[Step 1]
Agent is thinking...
Thought: Group by gender and compute mean age.
--- CODE ---
print(df.groupby('gender')['age'].mean())
------------
--- OUTPUT ---
gender
Female    27.3
Male      29.1
--------------

[Step 2]
Assistant: The average age of women is 27.3 and men is 29.1.
```

---

## How it works

The agent runs in a loop:

1. User asks a question in plain English
2. LLM decides whether to write code or reply directly
3. If code → it gets executed in a sandboxed Python environment against your actual data
4. Output is fed back to the LLM
5. LLM repeats until it has a final answer

The LLM never guesses — it runs real Python on your real data.

```
User question
     ↓
  LLM decides: code or message?
     ↓              ↓
  write Python    reply directly
     ↓
  execute safely
     ↓
  feed output back to LLM
     ↓
  repeat until final answer
```

---

## Quickstart

### Option A — Run from source

**Requirements:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/YOUR_USERNAME/data-analyst-agent
cd data-analyst-agent
uv sync
uv run main.py
```

### Option B — Download the .exe (Windows)

No Python needed. Download `data-analyst-agent.exe` from the [Releases](../../releases) page and run it directly.

---

## Backends

### LM Studio (local)
- Download [LM Studio](https://lmstudio.ai) and load any model
- Start the local server (default port: 1234)
- Select option `[1]` when prompted
- Works fully offline — your data never leaves your machine

### Groq (cloud)
- Get a free API key at [console.groq.com/keys](https://console.groq.com/keys)
- Select option `[2]` when prompted and paste your key
- Recommended model: `llama-3.3-70b-versatile`

| Model | Speed | Quality |
|---|---|---|
| llama-3.3-70b-versatile | Fast | ⭐ Best |
| llama3-70b-8192 | Fast | Great |
| llama3-8b-8192 | Fastest | Good |
| mixtral-8x7b-32768 | Medium | Good |
| gemma2-9b-it | Fast | Good |

---

## Code execution safety

User code runs in a sandboxed executor (`executor.py`) that blocks:

- File system access (`open`, `os`, `shutil`)
- Network access (`requests`, `httpx`, `socket`, `urllib`)
- Dangerous builtins (`eval`, `exec`, `compile`)
- Subprocess spawning (`subprocess`, `multiprocessing`)

The agent can only use `pandas` and standard math/data libraries.

---

## Build the .exe yourself

```bash
uv add pyinstaller
pyinstaller --onefile --console --add-data "executor.py;." main.py
# output: dist/main.exe
```

---

## Project structure

```
├── main.py          # Agent loop, provider selection, CLI
├── executor.py      # Sandboxed Python code execution
├── pyproject.toml   # Dependencies (uv)
└── README.md
```

---

## Dependencies

- `openai` — API client (works with both LM Studio and Groq)
- `pydantic` — structured LLM output parsing
- `pandas` — data analysis inside the sandbox
