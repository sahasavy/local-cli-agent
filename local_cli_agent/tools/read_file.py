"""
Tool: read_file

Reads the contents of a file so the LLM can analyse or summarise it.
This is the cornerstone of the "summarisation" capability: the tool fetches
the raw text, and the LLM itself produces the summary in its response.
"""

from pathlib import Path

from .base import BaseTool


class ReadFileTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a file. Use this when you need to "
            "summarise, analyse, or answer questions about a file's contents. "
            f"Paths are relative to workspace: {self._workspace_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace, or absolute).",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to return. Defaults to 200.",
                },
            },
            "required": ["file_path"],
        }

    def execute(self, **kwargs) -> str:
        raw_path: str = kwargs["file_path"]
        max_lines: int = kwargs.get("max_lines", 200)

        path = Path(raw_path)
        if not path.is_absolute():
            path = self._workspace_dir / path

        if not path.exists():
            return f"Error: file '{path}' not found."
        if not path.is_file():
            return f"Error: '{path}' is not a regular file."

        try:
            text = path.read_text(errors="ignore")
        except PermissionError:
            return f"Error: permission denied reading '{path}'."

        lines = text.splitlines()
        total = len(lines)
        truncated = lines[:max_lines]

        result = "\n".join(truncated)
        if total > max_lines:
            result += f"\n\n[... truncated: showing {max_lines} of {total} lines]"

        return f"File: {path}  ({total} lines)\n\n{result}"
