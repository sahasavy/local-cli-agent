"""
Tool: create_note

Creates a markdown note and saves it to the configured notes directory.
The LLM generates the note content; this tool writes it to disk.
"""

from datetime import datetime
from pathlib import Path

from .base import BaseTool


class CreateNoteTool(BaseTool):

    def __init__(self, notes_dir: Path):
        self._notes_dir = notes_dir

    @property
    def name(self) -> str:
        return "create_note"

    @property
    def description(self) -> str:
        return (
            "Create a new markdown note file and save it to disk. "
            f"Notes are saved in: {self._notes_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the note.",
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Markdown body of the note. "
                        "Do NOT include the title heading — it is added automatically."
                    ),
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for categorisation.",
                },
            },
            "required": ["title", "content"],
        }

    def execute(self, **kwargs) -> str:
        title: str = kwargs["title"]
        content: str = kwargs["content"]
        tags: list[str] = kwargs.get("tags", [])

        self._notes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in title.lower())
        slug = "-".join(part for part in slug.split("-") if part)  # collapse runs of -
        filename = f"{timestamp.strftime('%Y%m%d')}-{slug}.md"
        filepath = self._notes_dir / filename

        lines = [
            f"# {title}",
            "",
            f"**Date:** {timestamp.strftime('%Y-%m-%d %H:%M')}",
        ]
        if tags:
            lines.append(f"**Tags:** {', '.join(tags)}")
        lines += ["", "---", "", content, ""]

        filepath.write_text("\n".join(lines))
        return f"Note created: {filepath}"
