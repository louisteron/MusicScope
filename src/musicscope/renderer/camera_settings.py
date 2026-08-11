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

    @property
    def enabled(self) -> bool:
        """Whether the live camera should replace the CRT background."""
        return self.mode is BackgroundMode.CAMERA

    def cycle(self, direction: int) -> None:
        """Select the next or previous background."""
        modes = tuple(BackgroundMode)
        self.mode = modes[(modes.index(self.mode) + direction) % len(modes)]
