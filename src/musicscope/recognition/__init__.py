"""Music-identification boundary and track metadata models."""

from musicscope.recognition.engine import RecognitionEngine
from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.recognition.provider import RecognitionProvider
from musicscope.recognition.workflow import IdentificationResult, IdentificationWorkflow

__all__ = [
    "AudioClip",
    "IdentificationResult",
    "IdentificationWorkflow",
    "RecognitionEngine",
    "RecognitionProvider",
    "RecognizedTrack",
]
