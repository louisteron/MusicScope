"""Tests for asynchronous lyric preparation before CD playback."""

from threading import Event

from musicscope.lyrics.service import LyricsService
from musicscope.recognition.models import RecognizedTrack


class EmptyLyricsSource:
    """A source that conclusively finds no synchronized lyrics."""

    def find(self, _track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        return ()


def test_lyrics_service_calls_ready_callback_when_no_lyrics_exist() -> None:
    """CD playback can start once an empty lyric lookup has completed."""
    completed = Event()
    received: list[tuple[tuple[float, str], ...]] = []
    service = LyricsService(EmptyLyricsSource(), received.append)

    service.load(
        RecognizedTrack(title="United in Grief", artist="Kendrick Lamar"),
        on_ready=lambda lines: completed.set() if lines == () else None,
    )

    assert completed.wait(timeout=1.0)
    assert received == [(), ()]
