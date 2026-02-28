import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralised configuration loaded from environment variables / .env file."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    DEFAULT_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", str(Path.home())))
    NOTES_DIR: Path = Path(os.getenv("NOTES_DIR", str(Path.home() / "notes")))

    MAX_TOOL_ITERATIONS: int = int(os.getenv("MAX_TOOL_ITERATIONS", "10"))
