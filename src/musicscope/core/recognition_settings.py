"""Runtime selection state for MusicScope metadata sources."""

from dataclasses import dataclass

from musicscope.config import RecognitionMode


@dataclass(slots=True)
class RecognitionSettings:
    """Store and cycle the metadata mode exposed by the settings menu."""

    mode: RecognitionMode
    status: str = "IDLE"

    def cycle_mode(self, direction: int) -> None:
        """Select the next available metadata source."""
        modes = tuple(RecognitionMode)
        self.mode = modes[(modes.index(self.mode) + direction) % len(modes)]

    @property
    def label(self) -> str:
        """Return a concise label that fits the overlay."""
        return "LOCAL CD" if self.mode is RecognitionMode.LOCAL_CD else self.mode.upper()

    def set_status(self, status: str) -> None:
        """Publish a compact runtime state for the on-screen audio panel."""
        self.status = status
