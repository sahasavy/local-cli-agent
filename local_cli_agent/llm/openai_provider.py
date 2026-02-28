"""
OpenAI provider — wraps the OpenAI chat-completions API with tool calling.

OpenAI tool-calling flow:
  1. Send messages + tool definitions via the ``tools`` parameter.
  2. If the model wants to call tools, the assistant message includes
     ``tool_calls`` — each with an ``id``, function ``name``, and JSON
     ``arguments``.
  3. We execute the tools locally, then append one ``role: "tool"`` message
     **per tool call**, keyed by ``tool_call_id``.
  4. Send the updated conversation back; the model synthesises a final answer.
"""

import json

from openai import OpenAI

from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolResult


class OpenAIProvider(BaseLLMProvider):

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    # -- schema conversion ---------------------------------------------------

    def get_tool_schemas(self, tools: list) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    # -- chat ----------------------------------------------------------------

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        kwargs: dict = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return LLMResponse(text=message.content, tool_calls=tool_calls)

    # -- message formatting --------------------------------------------------

    def format_assistant_message(self, response: LLMResponse) -> dict:
        msg: dict = {"role": "assistant", "content": response.text}
        if response.has_tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in response.tool_calls
            ]
        return msg

    def format_tool_results(self, results: list[ToolResult]) -> list[dict]:
        """OpenAI expects one ``role: tool`` message per tool call."""
        return [
            {
                "role": "tool",
                "tool_call_id": r.tool_call_id,
                "content": r.output,
            }
            for r in results
        ]
