"""Tests for root-level dotenv configuration."""

import os

from musicscope.config.environment import load_project_environment


def test_project_environment_loads_credentials_from_dotenv(tmp_path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("MUSICSCOPE_ACRCLOUD_HOST=example.acrcloud.com\n")
    monkeypatch.delenv("MUSICSCOPE_ACRCLOUD_HOST", raising=False)

    assert load_project_environment(dotenv)
    assert os.environ["MUSICSCOPE_ACRCLOUD_HOST"] == "example.acrcloud.com"


def test_project_environment_does_not_override_real_environment(tmp_path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("MUSICSCOPE_ACRCLOUD_HOST=file-value\n")
    monkeypatch.setenv("MUSICSCOPE_ACRCLOUD_HOST", "shell-value")

    load_project_environment(dotenv)

    assert os.environ["MUSICSCOPE_ACRCLOUD_HOST"] == "shell-value"
