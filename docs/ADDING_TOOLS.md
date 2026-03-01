# Adding New Tools

Here's how we add new tools to the agent.

---

## The Tool Interface

Every tool extends `BaseTool` and implements four things:

| Member              | Type            | Purpose                                          |
|---------------------|-----------------|--------------------------------------------------|
| `name`              | `str` property  | Unique identifier the LLM uses to call this tool |
| `description`       | `str` property  | Natural-language explanation the LLM reads       |
| `parameters`        | `dict` property | JSON Schema describing expected arguments        |
| `execute(**kwargs)` | method          | Runs the tool, returns a plain-text result       |

---

## Step-by-Step Example: `list_directory` Tool

Let's walk through building a tool that lists the contents of a directory.

### 1. Create the file

```python
# local_cli_agent/tools/list_directory.py

from pathlib import Path
from .base import BaseTool


class ListDirectoryTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return (
            "List the files and sub-directories in a given directory. "
            f"Paths are relative to: {self._workspace_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (relative to workspace).",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with '.'). Default: false.",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs) -> str:
        rel_path = kwargs["path"]
        show_hidden = kwargs.get("show_hidden", False)

        target = self._workspace_dir / rel_path
        if not target.exists():
            return f"Error: '{target}' does not exist."
        if not target.is_dir():
            return f"Error: '{target}' is not a directory."

        entries = sorted(target.iterdir())
        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        lines = []
        for entry in entries:
            kind = "dir" if entry.is_dir() else "file"
            lines.append(f"  [{kind}]  {entry.name}")

        if not lines:
            return "Directory is empty."
        return f"Contents of {rel_path}/:\n" + "\n".join(lines)
```

### 2. Register the tool

In `local_cli_agent/main.py`, import it and drop it into the tools list:

```python
from .tools.list_directory import ListDirectoryTool

tools = [
    FileSearchTool(workspace_dir=Config.WORKSPACE_DIR),
    CreateNoteTool(notes_dir=Config.NOTES_DIR),
    ReadFileTool(workspace_dir=Config.WORKSPACE_DIR),
    ListDirectoryTool(workspace_dir=Config.WORKSPACE_DIR),  # new
]
```

### 3. Try it out

```
You > List the contents of the src directory

  tool → list_directory {'path': 'src'}
  ✓ done

╭─ Agent ─────────────────────────────────────╮
│ Here's what's in the src/ directory:        │
│   [dir]   components                        │
│   [dir]   utils                             │
│   [file]  main.py                           │
│   [file]  config.py                         │
╰─────────────────────────────────────────────╯
```

---

## Tips for Good Tool Design

### Write clear descriptions

The `description` and parameter descriptions are the LLM's *only* way to understand a tool. Be specific:

```python
# Bad - too vague
"Search for stuff"

# Good - specific and actionable
"Search for files in the workspace by filename glob pattern and/or text content. Case-insensitive."
```

### Return structured text

The LLM reads tool output as plain text, so formatting matters:

```python
# Bad
return str(results)

# Good
return f"Found {len(results)} items:\n" + "\n".join(f"  - {r}" for r in results)
```

### Handle errors gracefully

Return error messages as strings rather than raising exceptions. This lets the LLM reason about what went wrong and
potentially recover:

```python
if not path.exists():
    return f"Error: file '{path}' not found."
```

### Keep tools focused

Each tool should do **one thing well**. We'd rather have multiple small tools than one complex tool - the LLM is
surprisingly good at chaining them together.

---

## Built-in Tools Reference

We currently ship 12 tools:

| Tool             | Description                                           |
|------------------|-------------------------------------------------------|
| `search_files`   | Search workspace by filename glob and/or text content |
| `create_note`    | Create a markdown note in the notes directory         |
| `read_file`      | Read file contents for analysis or summarisation      |
| `write_file`     | Create or overwrite a file with given content         |
| `list_directory` | List files and sub-directories                        |
| `word_count`     | Count words in a given text                           |
| `run_shell`      | Execute a shell command and return stdout/stderr      |
| `web_search`     | Search the web using the Tavily API                   |
| `calculator`     | Safely evaluate mathematical expressions              |
| `git_status`     | Show the current Git status of the workspace          |
| `http_request`   | Make an HTTP GET/POST request and return the response |
| `database_query` | Execute SQL queries against a SQLite database         |

---

## More Tool Ideas to Try

| Tool             | Description                                      |
|------------------|--------------------------------------------------|
| `send_email`     | Send an email via SMTP                           |
| `json_transform` | Parse, query, and transform JSON data (jq-style) |
| `regex_replace`  | Find and replace with regex across file contents |
| `system_info`    | Return CPU, memory, disk, and OS information     |
| `cron_schedule`  | Create or list cron jobs                         |
| `docker_status`  | List running Docker containers and images        |
