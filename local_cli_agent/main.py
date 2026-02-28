"""
CLI entry point for the Local CLI Agent.

Provides both interactive (REPL) and single-shot modes.
"""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import Agent
from .config import Config
from .llm.anthropic_provider import AnthropicProvider
from .llm.openai_provider import OpenAIProvider
from .tools.create_note import CreateNoteTool
from .tools.file_search import FileSearchTool
from .tools.read_file import ReadFileTool

console = Console()


def _build_agent(provider_name: str) -> Agent:
    """Construct an Agent wired to the chosen LLM provider and all tools."""

    if provider_name == "openai":
        if not Config.OPENAI_API_KEY:
            console.print("[red]Error: OPENAI_API_KEY is not set. Check your .env file.[/red]")
            raise SystemExit(1)
        provider = OpenAIProvider(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
        )
    elif provider_name == "anthropic":
        if not Config.ANTHROPIC_API_KEY:
            console.print("[red]Error: ANTHROPIC_API_KEY is not set. Check your .env file.[/red]")
            raise SystemExit(1)
        provider = AnthropicProvider(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.ANTHROPIC_MODEL,
        )
    else:
        console.print(f"[red]Unknown provider '{provider_name}'. Use 'openai' or 'anthropic'.[/red]")
        raise SystemExit(1)

    tools = [
        FileSearchTool(workspace_dir=Config.WORKSPACE_DIR),
        CreateNoteTool(notes_dir=Config.NOTES_DIR),
        ReadFileTool(workspace_dir=Config.WORKSPACE_DIR),
    ]

    return Agent(
        provider=provider,
        tools=tools,
        max_iterations=Config.MAX_TOOL_ITERATIONS,
    )


def _print_help() -> None:
    console.print(
        Panel(
            "[bold]Commands[/bold]\n\n"
            "  [green]help[/green]    Show this message\n"
            "  [green]clear[/green]   Reset conversation history\n"
            "  [green]quit[/green]    Exit the agent  (also: exit, q, Ctrl-C)\n\n"
            "[bold]Example queries[/bold]\n\n"
            '  "Find all Python files in my workspace"\n'
            '  "Create a note about Docker best practices"\n'
            '  "Summarise the file report.txt"\n'
            '  "Search for files containing TODO"\n',
            title="Help",
            border_style="green",
        )
    )


@click.command()
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["openai", "anthropic"]),
    help="LLM provider (overrides LLM_PROVIDER in .env).",
)
@click.option(
    "--query", "-q",
    default=None,
    type=str,
    help="Run a single query and exit (non-interactive mode).",
)
def main(provider: str | None, query: str | None) -> None:
    """Local CLI Agent — a natural-language powered assistant."""

    provider_name = provider or Config.DEFAULT_PROVIDER

    console.print(
        Panel(
            f"[bold]Local CLI Agent[/bold]\n"
            f"Provider: [cyan]{provider_name}[/cyan]  |  "
            f"Workspace: [cyan]{Config.WORKSPACE_DIR}[/cyan]\n"
            f"Type [bold green]help[/bold green] for usage, "
            f"[bold red]quit[/bold red] to exit.",
            title="Welcome",
            border_style="blue",
        )
    )

    agent = _build_agent(provider_name)

    if query:
        response = agent.run(query)
        console.print()
        console.print(Panel(Markdown(response), border_style="blue", title="Agent"))
        return

    while True:
        try:
            user_input = console.input("\n[bold green]You >[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input.lower() == "help":
            _print_help()
            continue
        if user_input.lower() == "clear":
            agent = _build_agent(provider_name)
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        console.print()
        response = agent.run(user_input)
        console.print()
        console.print(Panel(Markdown(response), border_style="blue", title="Agent"))


if __name__ == "__main__":
    main()
