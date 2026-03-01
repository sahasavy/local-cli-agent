"""
Tool: word_count

A tool that counts the number of words in a given text or file.
"""

from .base import BaseTool


class WordCountTool(BaseTool):

    @property
    def name(self) -> str:
        return "word_count"

    @property
    def description(self) -> str:
        return "Count the number of words in a given text or file."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to count words in.",
                },
            },
            "required": ["text"],
        }

    def execute(self, **kwargs) -> str:
        text = kwargs["text"]
        count = len(text.split())
        return f"Word count: {count}"
