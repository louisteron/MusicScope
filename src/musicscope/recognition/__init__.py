"""Music-identification boundary and track metadata models."""

from musicscope.recognition.audd import AudDCredentials, AudDProvider
from musicscope.recognition.engine import RecognitionEngine
from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.recognition.provider import RecognitionProvider

__all__ = [
    "AudioClip",
    "AudDCredentials",
    "AudDProvider",
    "CdMetadataService",
    "CdMetadataUnavailable",
    "IdentificationResult",
    "IdentificationWorkflow",
    "MusicBrainzCdLookup",
    "RecognitionEngine",
    "RecognitionProvider",
    "RecognizedTrack",
]


def __getattr__(name: str) -> type[object]:
    """Load workflow types lazily to avoid an artwork/recognition import cycle."""
    if name in {"IdentificationResult", "IdentificationWorkflow"}:
        from musicscope.recognition.workflow import IdentificationResult, IdentificationWorkflow

        return {
            "IdentificationResult": IdentificationResult,
            "IdentificationWorkflow": IdentificationWorkflow,
        }[name]
    if name in {"CdMetadataService", "CdMetadataUnavailable", "MusicBrainzCdLookup"}:
        from musicscope.recognition.cd import CdMetadataUnavailable, MusicBrainzCdLookup
        from musicscope.recognition.cd_service import CdMetadataService

        return {
            "CdMetadataService": CdMetadataService,
            "CdMetadataUnavailable": CdMetadataUnavailable,
            "MusicBrainzCdLookup": MusicBrainzCdLookup,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
