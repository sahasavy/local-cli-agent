"""
Tool: search_files

Searches the workspace for files by name pattern (glob) and/or content
(case-insensitive substring match).
"""

import fnmatch
import os
from pathlib import Path

from .base import BaseTool

MAX_RESULTS = 50
SKIP_DIRS = frozenset({".git", "__pycache__", "node_modules", ".venv", "venv", ".idea"})


class FileSearchTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return (
            "Search for files in the workspace directory by filename pattern "
            "and/or text content. "
            f"Workspace root: {self._workspace_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "Filename glob pattern, e.g. '*.py', 'README*', '*.txt'. "
                        "Defaults to '*' (all files)."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "Text to search for inside file contents (case-insensitive).",
                },
                "directory": {
                    "type": "string",
                    "description": "Sub-directory to search in, relative to the workspace root.",
                },
            },
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern", "*")
        content_query = kwargs.get("content")
        subdir = kwargs.get("directory", "")

        search_root = self._workspace_dir / subdir
        if not search_root.exists():
            return f"Error: directory '{search_root}' does not exist."

        matches: list[str] = []
        for root, dirs, files in os.walk(search_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in files:
                if filename.startswith("."):
                    continue
                if not fnmatch.fnmatch(filename, pattern):
                    continue

                filepath = Path(root) / filename
                rel_path = filepath.relative_to(self._workspace_dir)

                if content_query:
                    try:
                        text = filepath.read_text(errors="ignore")
                        if content_query.lower() not in text.lower():
                            continue
                        hit_lines = [
                            i + 1
                            for i, line in enumerate(text.splitlines())
                            if content_query.lower() in line.lower()
                        ]
                        matches.append(f"{rel_path}  (matching lines: {hit_lines[:10]})")
                    except (PermissionError, OSError):
                        continue
                else:
                    matches.append(str(rel_path))

                if len(matches) >= MAX_RESULTS:
                    break
            if len(matches) >= MAX_RESULTS:
                break

        if not matches:
            return "No files found matching the given criteria."

        header = f"Found {len(matches)} file(s):\n"
        return header + "\n".join(f"  - {m}" for m in matches)
