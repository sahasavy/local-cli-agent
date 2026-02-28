"""
Abstract base class for agent tools.

Every tool exposes three pieces of metadata that the LLM needs:
  - name:        unique identifier used in tool-call requests
  - description: natural-language explanation the LLM reads to decide when to use the tool
  - parameters:  JSON Schema describing the expected arguments

And one method:
  - execute(**kwargs) -> str:  runs the tool and returns a text result
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """Return a JSON Schema object describing this tool's inputs."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Run the tool and return a plain-text result string."""
        ...
