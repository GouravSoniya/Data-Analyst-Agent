# Data Analyst Agent

An intelligent AI-powered data analysis tool that transforms natural language questions into executable Python code and delivers accurate, real-time insights from your CSV files. No hallucinations—just real computation.

LIVE DEMO : https://data-analyst-agent-xskgltunuwo6copquqldw9.streamlit.app/


[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Code style: Streamlit](https://img.shields.io/badge/Web%20UI-Streamlit-FF4B4B)](https://streamlit.io/)

## Overview

Data Analyst Agent is a multi-interface system that combines the power of large language models (LLMs) with safe, sandboxed Python execution. Ask questions about your data in plain English, and the agent writes real Python code, executes it safely, and delivers accurate insights backed by computation—not hallucinations.

### Key Features

[PASS] **Dual Interfaces**
- CLI for power users and automation
- Streamlit web app for interactive analysis

[PASS] **Flexible Backend Options**
- **LM Studio**: Fully local, no internet required, complete data privacy
- **Groq API**: Free cloud-based, ultra-fast inference

[PASS] **Real Code Execution**
- Agent writes actual Python code instead of guessing
- Results are guaranteed accurate based on your real data
- No hallucinations—every answer backed by computation

[PASS] **Production-Ready Safety**
- Sandboxed code execution environment
- Blocks file system, network, and dangerous operations
- Safe library support (pandas, numpy, matplotlib)

[PASS] **Multi-Step Reasoning**
- Agent can iterate and refine answers
- Automatic handling of code execution errors
- Smart fallback to plain-text responses when appropriate

---

## Use Cases

- **Business Intelligence**: Analyze sales trends, customer demographics, financial metrics
- **Data Exploration**: Understand data distributions, relationships, and anomalies
- **Quick Prototyping**: Validate hypotheses without writing boilerplate code
- **Educational**: Learn data analysis by watching the AI write code
- **Automation**: Build scripts that generate insights automatically

---

## Quick Start

### Installation

**Requirements:**
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (optional but recommended)

#### Option A: From Source (Recommended)

```bash
git clone https://github.com/GouravSoniya/Data-Analyst-Agent.git
cd Data-Analyst-Agent
uv sync
uv run main.py
```

#### Option B: With pip

```bash
git clone https://github.com/GouravSoniya/Data-Analyst-Agent.git
cd Data-Analyst-Agent
pip install -r requirements.txt
python main.py
```

#### Option C: Windows Executable

No Python required! Download the compiled `.exe` from the [Releases](../../releases) page.

---

## Usage

### CLI Interface (main.py)

```bash
uv run main.py
```

**Interactive Workflow:**

1. **Select Backend**
   - Option `[1]`: LM Studio (local, offline)
   - Option `[2]`: Groq (free API, online)

2. **Provide CSV File**
   - Enter the path to your CSV file
   - Agent displays a preview of the first 3 rows

3. **Ask Questions**
   - Type natural language questions about your data
   - Agent iterates until it has a final answer
   - Type `exit` or `quit` to stop

**Example Session:**

```
--- Data Analyst Agent ---

Select backend:
  [1] LM Studio  (local, no internet needed)
  [2] Groq        (free API, needs internet)

Enter 1 or 2: 2
Enter your Groq API key: gsk_...

[PASS] Using Groq with llama-3.3-70b-versatile

CSV path: sales_data.csv

You: What is the average transaction by product category?

[Step 1]

Agent is thinking...
Thought: Group by product category and calculate mean transaction amount
--- CODE ---
print(df.groupby('category')['amount'].mean().round(2))
------------
--- OUTPUT ---
category
Electronics    450.75
Clothing       125.30
Home           89.50
--------------

[Step 2]
Assistant: The average transaction by product category is:
- Electronics: $450.75
- Clothing: $125.30
- Home: $89.50
```

### Web Interface (app.py)

```bash
uv run streamlit run app.py
```

**Features:**
- Upload CSV files directly via web interface
- Interactive chat-based data exploration
- Real-time code and output display
- Data preview sidebar
- Clear chat history button

---

## How It Works

The agent operates in an intelligent loop:

```
User Question (Plain English)
     ↓
   LLM Analysis
     ↓
   ┌─────────────────────┐
   │                     │
   ↓                     ↓
Write Python Code    Direct Reply
   ↓                     ↓
Execute Safely    Return Answer
   ↓                     │
Feed Output Back ←──────┘
   ↓
Repeat or Finalize
```

### Processing Steps

1. **Question Input**: User asks a question in natural language
2. **LLM Decision**: Model decides whether code execution or direct reply is needed
3. **Code Generation**: If needed, LLM generates safe, executable Python code
4. **Sandboxed Execution**: Code runs in isolated environment with restricted permissions
5. **Output Analysis**: Results fed back to LLM for interpretation
6. **Iteration**: Process repeats until final answer is ready
7. **Response**: Final answer delivered to user with reasoning trail

---

## Backend Configuration

### LM Studio (Local & Private)

**Setup:**
1. Download [LM Studio](https://lmstudio.ai) from their website
2. Choose and download any GGUF model (e.g., Llama 2, Mistral)
3. Start the local server (Settings → Server tab, default port 1234)
4. Select `[1]` when prompted in the agent

**Advantages:**
- [PASS] Completely offline—data never leaves your machine
- [PASS] Free to use
- [PASS] Full control over model choice
- [PASS] Privacy-focused

**Disadvantages:**
- Slower inference than cloud APIs
- Requires local computational resources

### Groq (Fast Cloud API)

**Setup:**
1. Get a free API key at [console.groq.com/keys](https://console.groq.com/keys)
2. Select `[2]` when prompted
3. Paste your API key

**Model Used:** `llama-3.3-70b-versatile` (fast, 70B parameter model)

**Advantages:**
- [PASS] Ultra-fast inference
- [PASS] Free tier available
- [PASS] No local setup required
- [PASS] Always available

**Disadvantages:**
- Requires internet connection
- API key needed
- Data sent to external server

---

## Security & Sandboxing

### Protected Execution Environment

The `executor.py` module provides strict sandboxing that **blocks**:

```
[X] File System Access
   - open(), os.remove(), shutil operations

[X] Network Access
   - requests, httpx, socket, urllib

[X] Dangerous Built-ins
   - eval, exec, compile, __import__

[X] Process Management
   - subprocess, multiprocessing, threading

[X] Other Risks
   - pickle (deserialization attacks)
   - ctypes, cffi (low-level access)
```

### Allowed Operations

```
[PASS] Data Analysis
   - pandas (DataFrames, groupby, aggregations)
   - numpy (arrays, calculations)
   - Standard library (math, statistics, collections)

[PASS] Visualization
   - matplotlib (basic plotting)

[PASS] Computation
   - Built-in functions (len, sum, max, min)
   - List/dict comprehensions
   - String and numeric operations
```

### Safety Checks

1. **AST Parsing**: Code analyzed before execution
2. **Module Whitelist**: Only safe imports allowed
3. **Attribute Blocking**: Dangerous methods blocked
4. **I/O Redirection**: stdout/stderr captured
5. **Exception Handling**: Errors logged safely

---

## Project Structure

```
Data-Analyst-Agent/
├── main.py              # CLI interface & agent loop
├── app.py               # Streamlit web interface
├── executor.py          # Safe code execution sandbox
├── pyproject.toml       # Project metadata & dependencies
├── uv.lock              # Locked dependency versions
├── .python-version      # Python version specification
├── launch.bat           # Windows launcher script
└── README.md            # This file
```

### Core Modules

**main.py** (CLI Agent)
- Provider selection (LM Studio vs Groq)
- CSV file loading
- Multi-step agent loop
- User interaction handling

**app.py** (Streamlit Web App)
- File upload interface
- Interactive chat UI
- Real-time code display
- Session state management

**executor.py** (Sandbox)
- Safe code execution
- Security checks and validation
- Output capture
- Error handling

---

## Dependencies

```
Core:
- openai: OpenAI-compatible API client (works with LM Studio & Groq)
- pydantic: Structured output validation
- pandas: Data manipulation and analysis
- numpy: Numerical computing

Web UI:
- streamlit: Web app framework
- dotenv: Environment variable management

Data Analysis:
- matplotlib: Visualization support

Development:
- pyinstaller: Executable packaging
- uv: Fast Python package manager
```

For complete dependency list, see `pyproject.toml`.

---

## Advanced Setup

### Build Windows Executable

Convert `main.py` to standalone `.exe` for distribution:

```bash
uv add pyinstaller
pyinstaller --onefile --console --add-data "executor.py;." main.py
# Output: dist/main.exe
```

### Deploy Streamlit Web App

**On Streamlit Cloud:**
1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Create new app, select your repository
4. Add `GROQ_API_KEY` to Streamlit Secrets

**On Custom Server:**
```bash
streamlit run app.py --server.port 8501
```

### Environment Variables

Create `.env` file:
```bash
GROQ_API_KEY=gsk_your_api_key_here
```

---

## Example Queries

```
# Financial Analysis
"What is the average revenue by region?"
"Show me the top 5 months by sales"
"Calculate year-over-year growth"

# Data Exploration
"How many unique customers do we have?"
"What's the distribution of order values?"
"Find outliers in the dataset"

# Data Cleaning
"Show me missing values by column"
"List duplicate rows"
"What are the data types?"

# Comparisons
"Compare Q1 vs Q2 sales"
"Which product has the highest margin?"
"What percentage of orders were refunded?"
```

---

## Troubleshooting

### Common Issues

**"Connection refused" with LM Studio**
- Ensure LM Studio is running and server is started
- Check that port 1234 is accessible
- Try `http://localhost:1234/v1` in browser

**"Invalid API key" with Groq**
- Verify key in [console.groq.com/keys](https://console.groq.com/keys)
- Check for extra whitespace
- Ensure `.env` file is in correct location

**"CSV file not found"**
- Use full path: `/home/user/data/file.csv`
- Check file permissions
- Ensure file is valid CSV format

**"Code execution blocked"**
- Some operations are intentionally blocked for security
- Use pandas/numpy instead of file operations
- Avoid network requests

---

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Additional LLM provider support (Claude, Ollama)
- [ ] Advanced visualization options
- [ ] Multi-file analysis
- [ ] Query caching and history export
- [ ] Performance optimizations
- [ ] Additional safety audit

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## Support & Feedback

- **Issues**: Open an issue on GitHub for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Feedback**: Share your experience and suggestions

---

## Future Roadmap

- [ ] Support for multiple file formats (JSON, Excel, SQL databases)
- [ ] Advanced charting and visualization library
- [ ] Model fine-tuning on domain-specific data
- [ ] REST API endpoint
- [ ] Batch processing for large datasets
- [ ] Query optimization and caching layer
- [ ] Mobile app interface

---

## Notes

- Data safety is paramount—code runs in a restricted sandbox
- LLM responses are deterministic (temperature set to 0.3)
- Maximum 10 agent steps per query to prevent infinite loops
- Keep CSV files reasonably sized for optimal performance

---

Made with love by [GouravSoniya](https://github.com/GouravSoniya)
