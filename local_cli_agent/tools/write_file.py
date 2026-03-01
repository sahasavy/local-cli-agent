"""
Tool: write_file

Creates or overwrites a file with the given content.
Parent directories are created automatically.
"""

from pathlib import Path

from .base import BaseTool


class WriteFileTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Create or overwrite a file with the given content. "
            "Parent directories are created automatically. "
            f"Paths are relative to workspace: {self._workspace_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path for the file (relative to workspace, or absolute).",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file.",
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to the file instead of overwriting. Default: false.",
                },
            },
            "required": ["file_path", "content"],
        }

    def execute(self, **kwargs) -> str:
        raw_path: str = kwargs["file_path"]
        content: str = kwargs["content"]
        append: bool = kwargs.get("append", False)

        path = Path(raw_path)
        if not path.is_absolute():
            path = self._workspace_dir / path

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(path, mode) as f:
                f.write(content)
        except PermissionError:
            return f"Error: permission denied writing to '{path}'."
        except Exception as exc:
            return f"Error writing file: {exc}"

        action = "Appended to" if append else "Written"
        size = path.stat().st_size
        return f"{action}: {path} ({size} bytes)"
