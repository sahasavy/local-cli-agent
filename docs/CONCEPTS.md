# Key Concepts

## What Is an AI Agent?

An AI agent is a program that uses a Large Language Model (LLM) as its **reasoning engine** to autonomously decide *what
actions to take* to fulfil a request. The key difference from a simple chatbot:

| Chatbot                       | Agent                                                     |
|-------------------------------|-----------------------------------------------------------|
| Receives prompt, returns text | Receives prompt, **decides** what to do                   |
| No side effects               | Can **execute tools** (read files, call APIs, write data) |
| Single LLM call               | **Iterative loop** - may call the LLM multiple times      |
| Stateless per turn            | Maintains context across tool calls                       |

## The Agent Loop

This is the core pattern behind every LLM-based agent - and it's exactly what we've implemented here:

```
User Input
    │
    ▼
┌──────────┐     ┌─────────────┐      ┌──────────┐
│   LLM    │────▶│ Tool Call?  │──Y──▶│ Execute  │
│ (reason) │     └─────────────┘      │  Tool    │
└──────────┘           │ N            └────┬─────┘
    ▲                  ▼                   │
    │           Final Response             │
    │                                      │
    └─────── feed result back ◄────────────┘
```

The LLM acts as the "brain" - it decides *which* tool to call, *what arguments* to pass, and *how* to interpret the
results. Our agent loop in `agent.py` simply orchestrates the back-and-forth.

## Tool Calling (Function Calling)

Modern LLMs (GPT-4o, Claude, etc.) natively support **tool calling**: they can output structured JSON requests to invoke
specific functions. This isn't string parsing or regex hacking - the LLM has been trained to produce well-formed tool
invocations.

```
USER INPUT: "Find all Python files in my project"
                    │
                    ▼
LLM decides:  call search_files(pattern="*.py")
                    │
                    ▼
Our agent executes the tool locally, returns results
                    │
                    ▼
LLM reads results and writes a human-friendly answer
```
