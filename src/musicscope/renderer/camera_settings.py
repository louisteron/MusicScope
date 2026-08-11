"""Runtime state for choosing the visual background."""

from dataclasses import dataclass
from enum import StrEnum


class BackgroundMode(StrEnum):
    """Available visual backgrounds."""

    CRT = "CRT"
    CAMERA = "CAMERA"


@dataclass(slots=True)
class CameraSettings:
    """Keep camera background selection separate from camera capture."""

    mode: BackgroundMode = BackgroundMode.CRT
    device_index: int = 0

    @property
    def enabled(self) -> bool:
        """Whether the live camera should replace the CRT background."""
        return self.mode is BackgroundMode.CAMERA

    def cycle(self, direction: int) -> None:
        """Select the next or previous background."""
        modes = tuple(BackgroundMode)
        self.mode = modes[(modes.index(self.mode) + direction) % len(modes)]

    def cycle_device(self, direction: int) -> None:
        """Choose one of the camera inputs exposed by the operating system."""
        self.device_index = (self.device_index + direction) % 8
