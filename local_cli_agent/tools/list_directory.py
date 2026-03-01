"""
Tool: list_directory

A tool that lists the contents of a directory.
"""

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
