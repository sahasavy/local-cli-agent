# Local CLI Agent

A Python CLI agent that uses LLM APIs (OpenAI / Anthropic) with **tool calling** to handle local tasks - file
operations, shell commands, web search, math, Git, HTTP requests, database queries, and more.

I built this from scratch (no frameworks) to really understand how agentic AI works under the hood.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Adding New Tools](#adding-new-tools)
- [Configuration Reference](#configuration-reference)
- [Next Steps](#next-steps)

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    CLI Interface                         │
│                (main.py · Click · Rich)                  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                     Agent Loop                           │
│                     (agent.py)                           │
│                                                          │
│   1. User input  ──▶  LLM                                │
│   2. LLM decides:  respond  OR  call tool(s)             │
│   3. If tool call  ──▶  execute  ──▶  feed result back   │
│   4. Repeat until final text response                    │
└──────────┬───────────────────────────────┬───────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────┐   ┌──────────────────────────────────┐
│    LLM Providers    │   │              Tools               │
│                     │   │                                  │
│  ┌───────────────┐  │   │  ┌────────────────────────────┐  │
│  │    OpenAI     │  │   │  │  search_files              │  │
│  │  (GPT-4o)     │  │   │  │  Find files by name/text   │  │
│  └───────────────┘  │   │  └────────────────────────────┘  │
│  ┌───────────────┐  │   │  ┌────────────────────────────┐  │
│  │  Anthropic    │  │   │  │  create_note               │  │
│  │  (Claude)     │  │   │  │  Generate markdown notes   │  │
│  └───────────────┘  │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  read_file                 │  │
│                     │   │  │  Read files for analysis   │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  write_file                │  │
│                     │   │  │  Create / overwrite files  │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  run_shell                 │  │
│                     │   │  │  Execute shell commands    │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  git_status                │  │
│                     │   │  │  Show Git repo status      │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  calculator                │  │
│                     │   │  │  Evaluate math expressions │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  web_search                │  │
│                     │   │  │  Search the web (Tavily)   │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  http_request              │  │
│                     │   │  │  Make HTTP GET/POST        │  │
│                     │   │  └────────────────────────────┘  │
│                     │   │  ┌────────────────────────────┐  │
│                     │   │  │  database_query            │  │
│                     │   │  │  Run SQLite queries        │  │
│                     │   │  └────────────────────────────┘  │
└─────────────────────┘   └──────────────────────────────────┘
```

**Design principles:**

- **Provider abstraction** - we can swap between OpenAI and Anthropic with a single flag
- **Tool interface** - every tool implements the same base class, so adding new ones is straightforward
- **No frameworks** - raw SDK calls so we understand exactly what's happening

---

## Project Structure

```
local-cli-agent/
├── README.md
├── pyproject.toml                     ← packaging & dependencies
├── requirements.txt
├── .env.example                       ← template for API keys
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md                ← architecture deep-dive
│   └── ADDING_TOOLS.md                ← guide for writing custom tools
└── local_cli_agent/
    ├── __init__.py
    ├── config.py                      ← loads .env configuration
    ├── agent.py                       ← the agent loop (core logic)
    ├── main.py                        ← CLI entry point (Click + Rich)
    ├── llm/
    │   ├── __init__.py
    │   ├── base.py                    ← abstract LLM provider interface
    │   ├── openai_provider.py         ← OpenAI implementation
    │   └── anthropic_provider.py      ← Anthropic implementation
    └── tools/
        ├── __init__.py
        ├── base.py                    ← abstract tool interface
        ├── file_search.py             ← search_files tool
        ├── create_note.py             ← create_note tool
        ├── read_file.py               ← read_file tool
        ├── write_file.py              ← write_file tool
        ├── list_directory.py          ← list_directory tool
        ├── word_count.py              ← word_count tool
        ├── run_shell.py               ← run_shell tool
        ├── web_search.py              ← web_search tool (Tavily API)
        ├── calculator.py              ← calculator tool
        ├── git_status.py              ← git_status tool
        ├── http_request.py            ← http_request tool
        └── database_query.py          ← database_query tool (SQLite)
```

---

## Prerequisites

- **Python 3.10+** (we use `X | Y` union type syntax)
- An API key for at least one provider:
    - [OpenAI API key](https://platform.openai.com/api-keys)
    - [Anthropic API key](https://console.anthropic.com/settings/keys)

---

## Setup

### 1. Clone / navigate to the project

```bash
cd /path/to/local-cli-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -e .
```

This installs everything in **editable mode** - `openai`, `anthropic`, `click`, `rich`, and `python-dotenv` all come
along for the ride.

### 4. Set up API keys

```bash
cp .env.example .env
```

Open `.env` and drop in the API key(s). Set the workspace directory to wherever we want the agent to operate.

### 5. Run the agent

```bash
# Interactive mode (REPL)
local-cli-agent

# Single query mode
local-cli-agent --query "Find all Python files in my workspace"

# Use a specific provider
local-cli-agent --provider anthropic
```

---

## Usage

### Interactive Mode

```
$ local-cli-agent

╭─ Welcome ────────────────────────────────────────────────╮
│ Local CLI Agent                                          │
│ Provider: openai  |  Workspace: /Users/dev/workspace     │
│ Type help for usage, quit to exit.                       │
╰──────────────────────────────────────────────────────────╯

You > Find all Python files that contain "import requests"

  tool → search_files {'pattern': '*.py', 'content': 'import requests'}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ I found 3 Python files that import `requests`:           │
│   - src/api_client.py (line 2)                           │
│   - scripts/download.py (line 1)                         │
│   - tests/test_api.py (line 5)                           │
╰──────────────────────────────────────────────────────────╯

You > Create a note about Python virtual environments

  tool → create_note {'title': 'Python Virtual Environments', ...}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ Done! I've created a note at:                            │
│ ~/notes/20260228-python-virtual-environments.md          │
╰──────────────────────────────────────────────────────────╯

You > Summarise the file README.md

  tool → read_file {'file_path': 'README.md'}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ Here's a summary of README.md:                           │
│ The file describes a CLI agent project that...           │
╰──────────────────────────────────────────────────────────╯

You > What is the square root of 2 to the power of 10?

  tool → calculator {'expression': 'sqrt(2) ** 10'}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ sqrt(2) ** 10 = 32                                       │
╰──────────────────────────────────────────────────────────╯

You > Run ls -la in my workspace

  tool → run_shell {'command': 'ls -la'}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ Here's the directory listing:                            │
│   drwxr-xr-x  12 user  staff  384 Feb 28 10:00 .         │
│   -rw-r--r--   1 user  staff  2048 Feb 28 09:30 README   │
│   ...                                                    │
╰──────────────────────────────────────────────────────────╯

You > What is the git status of my workspace?

  tool → git_status {}
  ✓ done

╭─ Agent ──────────────────────────────────────────────────╮
│ You're on branch main with 2 modified files:             │
│   - src/config.py                                        │
│   - README.md                                            │
╰──────────────────────────────────────────────────────────╯
```

### Single Query Mode

```bash
local-cli-agent -q "Search for files named '*.yaml'"
```

### In-Session Commands

| Command | Action                                      |
|---------|---------------------------------------------|
| `help`  | Show available commands and example queries |
| `clear` | Reset conversation history (start fresh)    |
| `quit`  | Exit the agent (also: `exit`, `q`, Ctrl-C)  |

---

## How It Works

Here's what happens under the hood when we type a query:

### Step 1 - User Input

We type: `"Summarise the file report.txt"`

### Step 2 - LLM Reasoning

The agent sends our message along with tool definitions (JSON schemas) to the LLM. The LLM doesn't respond with plain
text - instead it fires back a **tool call request**:

```json
{
  "tool": "read_file",
  "arguments": {
    "file_path": "report.txt"
  }
}
```

### Step 3 - Tool Execution

The agent looks up the `read_file` tool, calls `tool.execute(file_path="report.txt")`, and gets the file contents back
as a string.

### Step 4 - Result Feedback

The agent sends the tool result back to the LLM as a new message in the conversation.

### Step 5 - Final Response

Now the LLM has the file contents in context. It generates a human-friendly summary and returns plain text, which the
agent displays.

If the LLM needs *multiple* tools (say, search for a file first, then read it), it loops through steps 2–4 until it
has everything it needs.

---

## Adding New Tools

Check out [docs/ADDING_TOOLS.md](docs/ADDING_TOOLS.md) for the full guide.

---

## Configuration Reference

All settings load from environment variables (or a `.env` file):

| Variable              | Default                    | Description                                                    |
|-----------------------|----------------------------|----------------------------------------------------------------|
| `LLM_PROVIDER`        | `openai`                   | Which LLM to use: `openai` or `anthropic`                      |
| `OPENAI_API_KEY`      | -                          | OpenAI API key                                                 |
| `OPENAI_MODEL`        | `gpt-4o-mini`              | OpenAI model name                                              |
| `ANTHROPIC_API_KEY`   | -                          | Anthropic API key                                              |
| `ANTHROPIC_MODEL`     | `claude-sonnet-4-20250514` | Anthropic model name                                           |
| `WORKSPACE_DIR`       | `$HOME`                    | Root directory the agent can search/read                       |
| `NOTES_DIR`           | `$HOME/notes`              | Where created notes are saved                                  |
| `MAX_TOOL_ITERATIONS` | `10`                       | Safety limit on consecutive tool calls                         |
| `TAVILY_API_KEY`      | -                          | API key for web_search tool ([tavily.com](https://tavily.com)) |
| `DATABASE_PATH`       | -                          | Default SQLite database path for database_query                |
