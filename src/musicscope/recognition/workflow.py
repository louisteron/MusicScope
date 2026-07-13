"""Application use case joining recognition and artwork acquisition."""

from dataclasses import dataclass

from musicscope.artwork.models import Artwork
from musicscope.artwork.pipeline import ArtworkPipeline
from musicscope.recognition.engine import RecognitionEngine
from musicscope.recognition.models import AudioClip, RecognizedTrack


@dataclass(frozen=True, slots=True)
class IdentificationResult:
    """Recognition metadata together with optional locally cached artwork."""

    track: RecognizedTrack
    artwork: Artwork | None


class IdentificationWorkflow:
    """Identify audio, then resolve its artwork through the independent pipeline."""

    def __init__(self, engine: RecognitionEngine, artwork_pipeline: ArtworkPipeline) -> None:
        self._engine = engine
        self._artwork_pipeline = artwork_pipeline

    def identify(self, clip: AudioClip) -> IdentificationResult | None:
        """Return track metadata and cached artwork for a recognized clip."""
        track = self._engine.identify(clip)
        if track is None:
            return None
        return IdentificationResult(track=track, artwork=self._artwork_pipeline.resolve(track))
