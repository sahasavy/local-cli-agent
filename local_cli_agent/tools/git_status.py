"""
Tool: git_status

Shows the current Git status of the workspace - branch, staged changes,
modified files, and untracked files.
"""

import subprocess
from pathlib import Path

from .base import BaseTool


class GitStatusTool(BaseTool):

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "git_status"

    @property
    def description(self) -> str:
        return (
            "Show the current Git status of the workspace - modified files, "
            "untracked files, current branch, and staging area. "
            f"Workspace: {self._workspace_dir}"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": (
                        "Sub-directory to check (relative to workspace). "
                        "Default: workspace root."
                    ),
                },
                "short": {
                    "type": "boolean",
                    "description": "Use short-format output. Default: false.",
                },
            },
        }

    def execute(self, **kwargs) -> str:
        subdir: str = kwargs.get("directory", "")
        short: bool = kwargs.get("short", False)

        target = self._workspace_dir / subdir if subdir else self._workspace_dir
        if not target.exists():
            return f"Error: directory '{target}' does not exist."

        cmd = ["git", "status"]
        if short:
            cmd.append("--short")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=target,
                timeout=10,
            )
        except FileNotFoundError:
            return "Error: git is not installed or not in PATH."
        except subprocess.TimeoutExpired:
            return "Error: git status timed out."

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not a git repository" in stderr:
                return f"Error: '{target}' is not inside a Git repository."
            return f"Git error: {stderr}"

        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=target,
            timeout=5,
        )
        branch = branch_result.stdout.strip() or "(detached HEAD)"

        output = result.stdout.strip()
        return f"Branch: {branch}\n\n{output}"
