"""Tests for the no-key Lyrics.ovh fallback."""

from urllib.error import HTTPError

from musicscope.lyrics.lyrics_ovh import LyricsOvhSource
from musicscope.lyrics.source import FallbackLyricsSource
from musicscope.recognition.models import RecognizedTrack


def test_lyrics_ovh_assigns_approximate_timestamps_to_plain_lyrics() -> None:
    requested: list[str] = []

    def get(url: str) -> bytes:
        requested.append(url)
        return b'{"lyrics":"First line\\n\\nSecond line"}'

    lines = LyricsOvhSource(get=get).find(RecognizedTrack(title="Song Name", artist="Artist Name"))

    assert lines == ((0.0, "First line"), (4.0, "Second line"))
    assert requested == ["https://api.lyrics.ovh/v1/Artist%20Name/Song%20Name"]


def test_fallback_uses_lyrics_ovh_when_lrclib_returns_no_lines() -> None:
    class EmptySource:
        def find(self, _track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
            return ()

    source = FallbackLyricsSource(
        (EmptySource(), LyricsOvhSource(get=lambda _url: b'{"lyrics":"Hi"}'))
    )

    assert source.find(RecognizedTrack(title="Song", artist="Artist")) == ((0.0, "Hi"),)


def test_lyrics_ovh_retries_an_exact_suggestion_after_a_missing_direct_lookup() -> None:
    calls: list[str] = []

    def get(url: str) -> bytes:
        calls.append(url)
        if "/suggest/" in url:
            return b'{"data":[{"title":"Song","artist":{"name":"Artist"}}]}'
        if url.endswith("/Artist/Song") and calls.count(url) == 1:
            raise HTTPError(url, 404, "Not found", {}, None)
        return b'{"lyrics":"Recovered line"}'

    lines = LyricsOvhSource(get=get).find(RecognizedTrack(title="Song", artist="Artist"))

    assert lines == ((0.0, "Recovered line"),)
    assert any("/suggest/Artist%20Song" in call for call in calls)
