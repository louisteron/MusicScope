"""Typed, immutable application settings."""

from dataclasses import dataclass
from enum import StrEnum

LOGO_NAMES = ("frog",)


class RecognitionMode(StrEnum):
    """Ways MusicScope can obtain music metadata."""

    AUDD = "audd"
    LOCAL_CD = "local-cd"
    OFF = "off"


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Runtime settings for one MusicScope session."""

    title: str = "MusicScope"
    width: int = 1280
    height: int = 720
    fullscreen: bool = False
    enable_audio: bool = True
    audio_device: str | None = None
    cd_device: str | None = None
    recognition_mode: RecognitionMode = RecognitionMode.LOCAL_CD
    logo: str = "frog"
    sample_rate: int = 44_100
    block_size: int = 1_024
    target_fps: int = 60

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            msg = "Window dimensions must be positive."
            raise ValueError(msg)
        if self.sample_rate <= 0 or self.block_size <= 0 or self.target_fps <= 0:
            msg = "Audio and frame settings must be positive."
            raise ValueError(msg)
        if self.logo not in LOGO_NAMES:
            msg = f"Logo must be one of: {', '.join(LOGO_NAMES)}."
            raise ValueError(msg)
