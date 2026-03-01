"""
Tool: run_shell

Executes a shell command in the workspace directory and returns stdout/stderr.
Includes a configurable timeout to prevent runaway processes.
"""

import subprocess
from pathlib import Path

from .base import BaseTool

TIMEOUT_SECONDS = 30


class RunShellTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "run_shell"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command and return its stdout and stderr. "
            f"Commands run in: {self._workspace_dir}. "
            "Use for tasks like listing processes, checking disk usage, "
            "running scripts, or any command-line operation."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": (
                        f"Maximum seconds to wait for the command to finish. "
                        f"Default: {TIMEOUT_SECONDS}."
                    ),
                },
            },
            "required": ["command"],
        }

    def execute(self, **kwargs) -> str:
        command: str = kwargs["command"]
        timeout: int = kwargs.get("timeout", TIMEOUT_SECONDS)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._workspace_dir,
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {timeout} seconds."
        except Exception as exc:
            return f"Error executing command: {exc}"

        output_parts = []
        if result.stdout.strip():
            output_parts.append(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr.strip():
            output_parts.append(f"STDERR:\n{result.stderr.strip()}")

        output = "\n\n".join(output_parts) if output_parts else "(no output)"
        return f"Exit code: {result.returncode}\n\n{output}"
