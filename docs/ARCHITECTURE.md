# Architecture Deep Dive

A closer look at how the project is structured and how data flows through it.

---

## Layered Architecture

We've split the project into three layers, each with a single job:

### Layer 1: CLI Interface (`main.py`)

Handles all user interaction - parsing CLI arguments, running the REPL loop, and rendering output with Rich. This layer
doesn't know or care about LLM APIs or tool implementations.

### Layer 2: Agent Loop (`agent.py`)

The orchestrator. It maintains conversation history, sends messages to the LLM provider, interprets tool-call requests,
dispatches tools, and feeds results back. This is where the "agentic" behaviour lives.

### Layer 3: Providers & Tools (`llm/`, `tools/`)

**LLM Providers** abstract the differences between the OpenAI and Anthropic APIs behind a uniform interface
(`BaseLLMProvider`). The agent never touches provider-specific message formats.

**Tools** are self-contained units with a name, description, parameter schema, and an `execute()` method. They don't
know anything about the LLM - they just take arguments and return strings. We currently ship 12 tools covering file
operations, shell execution, web search, math, Git, HTTP, and database queries.

---

## Message Flow (OpenAI Example)

```
messages = [
  { role: "system",    content: "You are a helpful CLI assistant..." },
  { role: "user",      content: "Find all .py files" },
  { role: "assistant", tool_calls: [{ id: "call_1", function: { name: "search_files", arguments: '{"pattern":"*.py"}' }}] },
  { role: "tool",      tool_call_id: "call_1", content: "Found 5 file(s):\n  - main.py\n  ..." },
  { role: "assistant", content: "I found 5 Python files: ..." },
]
```

Each round trip adds 2 messages: the assistant's tool-call request and the tool's result.

## Message Flow (Anthropic Example)

Anthropic uses a different schema - the system prompt is a separate parameter, tool calls are `tool_use` content blocks,
and tool results go in a single `user` message:

```
system = "You are a helpful CLI assistant..."
messages = [
  { role: "user",      content: "Find all .py files" },
  { role: "assistant", content: [{ type: "tool_use", id: "tu_1", name: "search_files", input: { pattern: "*.py" }}] },
  { role: "user",      content: [{ type: "tool_result", tool_use_id: "tu_1", content: "Found 5 file(s):..." }] },
  { role: "assistant", content: [{ type: "text", text: "I found 5 Python files: ..." }] },
]
```

Our `BaseLLMProvider` abstraction hides these differences so `agent.py` stays clean.

---

## Why No Framework?

Frameworks like LangChain and LlamaIndex are great, but they add layers of abstraction that can obscure what's actually
going on. By working with raw SDK calls, we get:

1. **A clear mental model** - we see every API call and message format
2. **Easier debugging** - no framework magic to trace through
3. **Transferable knowledge** - these patterns apply to *any* framework
4. **Full control** - we can customise the agent loop however we want

Once we understand these fundamentals, frameworks become *accelerators* rather than *black boxes*.

---

## Tool Schema Design

Tools expose their interface via **JSON Schema**, the same standard that LLM APIs use. Each tool provides:

```python
@property
def parameters(self) -> dict:
    return {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Filename glob pattern",
            },
        },
        "required": ["pattern"],
    }
```

The `description` fields matter a lot - they're the LLM's only way to figure out *when* and *how* to use a tool. Think
of it like explaining the parameter to a teammate who's never seen the code.

---

## Error Handling Strategy

Tool errors are caught and returned as plain text to the LLM rather than crashing the agent. This lets the LLM reason
about what went wrong and try a different approach - a key part of what makes the agent actually useful.

```python
try:
    result = tool.execute(**arguments)
except Exception as exc:
    result = f"Tool error ({type(exc).__name__}): {exc}"
```

The LLM might then respond with: "The file wasn't found. Could you double-check the filename?" - graceful degradation
powered by the model's reasoning.
