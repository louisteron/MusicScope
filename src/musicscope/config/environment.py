"""Project-local environment loading."""

from pathlib import Path

from dotenv import load_dotenv


def load_project_environment(dotenv_path: Path | None = None) -> bool:
    """Load the root ``.env`` file without overwriting real environment values."""
    path = dotenv_path or Path(__file__).resolve().parents[3] / ".env"
    return load_dotenv(dotenv_path=path, override=False)
