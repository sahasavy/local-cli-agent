"""
Abstract base for LLM providers.

Each provider (OpenAI, Anthropic) wraps its SDK and exposes a uniform
interface so the Agent loop never needs to know which API it is talking to.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    """A single tool invocation requested by the LLM."""

    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    """The output of a tool execution, tagged with the originating call."""

    tool_call_id: str
    tool_name: str
    output: str


@dataclass
class LLMResponse:
    """Normalised response from any LLM provider."""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLMProvider(ABC):
    """
    Contract that every LLM provider must implement.

    The key idea: the *Agent* owns the conversation loop and message history,
    but it delegates message formatting to the provider because OpenAI and
    Anthropic use different message schemas.
    """

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        """Send the conversation to the LLM and return a normalised response."""

    @abstractmethod
    def get_tool_schemas(self, tools: list) -> list[dict]:
        """Convert BaseTool list into the provider-specific schema format."""

    @abstractmethod
    def format_assistant_message(self, response: LLMResponse) -> dict:
        """Convert an LLMResponse into a provider-specific assistant message."""

    @abstractmethod
    def format_tool_results(self, results: list[ToolResult]) -> list[dict]:
        """Convert tool execution results into provider-specific messages."""
