"""Tests for settings validation."""

import pytest

from musicscope.config import AppSettings, RecognitionMode


def test_settings_reject_non_positive_window_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        AppSettings(width=0)


def test_settings_are_immutable() -> None:
    settings = AppSettings()
    with pytest.raises(AttributeError):
        settings.width = 10


def test_settings_reject_an_unknown_logo() -> None:
    with pytest.raises(ValueError, match="Logo"):
        AppSettings(logo="unknown")


def test_settings_accepts_the_frog_visual() -> None:
    assert AppSettings(logo="frog").logo == "frog"


def test_settings_supports_local_cd_metadata_mode() -> None:
    settings = AppSettings(recognition_mode=RecognitionMode.LOCAL_CD, cd_device="/dev/sr0")

    assert settings.recognition_mode is RecognitionMode.LOCAL_CD
