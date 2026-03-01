"""
agent.py - The core agent loop.

This is the most important file in the project.  It implements the
fundamental pattern behind *every* LLM-based agent:

    ┌─────────────────────────────────────────────────────────────┐
    │                        AGENT LOOP                           │
    │                                                             │
    │  1.  Receive natural-language input from the user           │
    │  2.  Send it (along with tool definitions) to the LLM       │
    │  3.  The LLM either:                                        │
    │        a) returns a final text response  →  done            │
    │        b) requests one or more tool calls                   │
    │  4.  Execute the requested tools locally                    │
    │  5.  Feed the tool results back to the LLM                  │
    │  6.  Go to step 3                                           │
    └─────────────────────────────────────────────────────────────┘

The LLM is the "brain" that decides *which* tools to call and *how* to
interpret the results.  The agent loop simply orchestrates the back-and-forth
until the LLM is satisfied it can answer the user.
"""

from rich.console import Console

from .llm.base import BaseLLMProvider, ToolResult
from .tools.base import BaseTool

console = Console()

SYSTEM_PROMPT = """\
You are a helpful CLI assistant with access to local tools.
Your job is to understand the user's natural language requests and use the
available tools to fulfil them.

Capabilities:
- **File Search** - find files by name pattern or text content in the workspace.
- **Note Creation** - generate and save well-structured markdown notes.
- **File Reading** - read file contents for summarisation or analysis.

Guidelines:
- Use tools whenever the task involves the filesystem.
- For summarisation, first read the file with read_file, then write a clear,
  concise summary in your response.
- For note creation, generate high-quality markdown and pass it to create_note.
- Explain what you did and present results clearly.
- If a request is ambiguous, ask for clarification rather than guessing.
"""


class Agent:
    """
    Orchestrates the LLM ↔ Tools conversation loop.

    Parameters
    ----------
    provider : BaseLLMProvider
        The LLM backend (OpenAI or Anthropic).
    tools : list[BaseTool]
        Tools the agent is allowed to use.
    max_iterations : int
        Safety cap on consecutive tool-call rounds to avoid infinite loops.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tools: list[BaseTool],
        max_iterations: int = 10,
    ):
        self.provider = provider
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self._tool_schemas = provider.get_tool_schemas(tools)

    def run(self, user_input: str) -> str:
        """
        Execute a single user turn through the agent loop.

        The conversation history (``self.messages``) is preserved across
        calls so the agent has memory within a session.
        """
        self.messages.append({"role": "user", "content": user_input})

        for _iteration in range(self.max_iterations):
            response = self.provider.chat(self.messages, self._tool_schemas)
            self.messages.append(
                self.provider.format_assistant_message(response)
            )

            if not response.has_tool_calls:
                return response.text or "(No response from the model.)"

            tool_results: list[ToolResult] = []
            for tc in response.tool_calls:
                output = self._execute_tool(tc.name, tc.arguments)
                tool_results.append(
                    ToolResult(
                        tool_call_id=tc.id,
                        tool_name=tc.name,
                        output=output,
                    )
                )

            self.messages.extend(
                self.provider.format_tool_results(tool_results)
            )

        return "Reached the maximum number of tool iterations. Try a simpler request."

    # -- private helpers ------------------------------------------------------

    def _execute_tool(self, name: str, arguments: dict) -> str:
        if name not in self.tools:
            return f"Error: unknown tool '{name}'."

        tool = self.tools[name]
        console.print(
            f"  [dim]tool →[/dim] [bold cyan]{name}[/bold cyan] "
            f"[dim]{arguments}[/dim]"
        )

        try:
            result = tool.execute(**arguments)
            console.print("  [dim green]✓ done[/dim green]")
            return result
        except Exception as exc:
            error = f"Tool error ({type(exc).__name__}): {exc}"
            console.print(f"  [dim red]✗ {error}[/dim red]")
            return error
