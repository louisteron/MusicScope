"""Typed, immutable application settings."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Runtime settings for one MusicScope session."""

    title: str = "MusicScope"
    width: int = 1280
    height: int = 720
    fullscreen: bool = False
    enable_audio: bool = True
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
