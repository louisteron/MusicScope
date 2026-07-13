"""Tests for the provider-independent identification workflow."""

from musicscope.artwork.models import Artwork
from musicscope.recognition.engine import RecognitionEngine
from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.recognition.workflow import IdentificationWorkflow


class FakeProvider:
    def identify(self, clip: AudioClip) -> RecognizedTrack:
        assert clip.content == b"clip"
        return RecognizedTrack("Song", "Artist")


class FakeArtworkPipeline:
    def resolve(self, track: RecognizedTrack) -> Artwork | None:
        assert track.title == "Song"
        return None


def test_workflow_connects_provider_neutral_engine_to_artwork_pipeline() -> None:
    workflow = IdentificationWorkflow(RecognitionEngine(FakeProvider()), FakeArtworkPipeline())
    result = workflow.identify(AudioClip(content=b"clip", sample_rate=44_100))
    assert result is not None
    assert result.track.artist == "Artist"
    assert result.artwork is None
