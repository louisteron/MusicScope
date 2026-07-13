"""Provider-neutral recognition use case."""

from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.recognition.provider import RecognitionProvider


class RecognitionEngine:
    """Delegate identification to the configured provider."""

    def __init__(self, provider: RecognitionProvider) -> None:
        self._provider = provider

    def identify(self, clip: AudioClip) -> RecognizedTrack | None:
        """Identify a clip while keeping callers independent from the provider."""
        return self._provider.identify(clip)
