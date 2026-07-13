"""Protocol implemented by each music-identification provider."""

from typing import Protocol

from musicscope.recognition.models import AudioClip, RecognizedTrack


class RecognitionProvider(Protocol):
    """Identify encoded audio without exposing provider-specific details."""

    def identify(self, clip: AudioClip) -> RecognizedTrack | None:
        """Return a track match, or ``None`` when no identification is available."""
