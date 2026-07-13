"""Tests for settings validation."""

import pytest

from musicscope.config import AppSettings


def test_settings_reject_non_positive_window_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        AppSettings(width=0)


def test_settings_are_immutable() -> None:
    settings = AppSettings()
    with pytest.raises(AttributeError):
        settings.width = 10
