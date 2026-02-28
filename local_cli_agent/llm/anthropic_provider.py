"""
Anthropic provider — wraps the Anthropic messages API with tool use.

Anthropic tool-use flow:
  1. Send messages + tool definitions via the ``tools`` parameter.
     The system prompt goes in a separate ``system`` kwarg (not in messages).
  2. If the model wants to call tools, the assistant message contains
     ``tool_use`` content blocks with ``id``, ``name``, and ``input``.
  3. We execute the tools locally, then send a single ``role: "user"``
     message containing one ``tool_result`` block per tool call.
  4. Send the updated conversation back; the model synthesises a final answer.

Key difference from OpenAI: tool results are bundled into **one** user
message (not one message per result).
"""

from anthropic import Anthropic

from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolResult


class AnthropicProvider(BaseLLMProvider):

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    # -- schema conversion ---------------------------------------------------

    def get_tool_schemas(self, tools: list) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    # -- chat ----------------------------------------------------------------

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        system_text: str | None = None
        filtered: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                filtered.append(m)

        kwargs: dict = {
            "model": self.model,
            "messages": filtered,
            "max_tokens": 4096,
        }
        if system_text:
            kwargs["system"] = system_text
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=block.input)
                )

        return LLMResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
        )

    # -- message formatting --------------------------------------------------

    def format_assistant_message(self, response: LLMResponse) -> dict:
        content: list[dict] = []
        if response.text:
            content.append({"type": "text", "text": response.text})
        for tc in response.tool_calls:
            content.append(
                {
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                }
            )
        return {"role": "assistant", "content": content}

    def format_tool_results(self, results: list[ToolResult]) -> list[dict]:
        """Anthropic expects all tool results in a single ``role: user`` message."""
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": r.tool_call_id,
                        "content": r.output,
                    }
                    for r in results
                ],
            }
        ]
