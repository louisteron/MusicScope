"""Tests for the optional Musixmatch synchronized-lyrics fallback."""

from musicscope.lyrics.musixmatch import MusixmatchLyricsSource
from musicscope.lyrics.source import FallbackLyricsSource
from musicscope.recognition.models import RecognizedTrack


def test_musixmatch_requests_lrc_subtitles_for_artist_and_title() -> None:
    requests: list[str] = []

    def get(url: str) -> bytes:
        requests.append(url)
        return b'{"message":{"body":{"subtitle":{"subtitle_body":"[00:01.20]Hello"}}}}'

    source = MusixmatchLyricsSource("secret", get=get)
    lines = source.find(RecognizedTrack(title="Song Name", artist="Artist Name"))

    assert lines == ((1.2, "Hello"),)
    assert "apikey=secret" in requests[0]
    assert "q_track=Song+Name" in requests[0]
    assert "q_artist=Artist+Name" in requests[0]
    assert "subtitle_format=lrc" in requests[0]


def test_fallback_uses_musixmatch_when_lrclib_returns_no_lines() -> None:
    class EmptySource:
        def find(self, _track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
            return ()

    class WorkingSource:
        def find(self, _track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
            return ((2.0, "Fallback lyric"),)

    source = FallbackLyricsSource((EmptySource(), WorkingSource()))

    assert source.find(RecognizedTrack(title="Song", artist="Artist")) == ((2.0, "Fallback lyric"),)


def test_musixmatch_rejects_a_non_success_api_status() -> None:
    source = MusixmatchLyricsSource(
        "secret",
        get=lambda _url: b'{"message":{"header":{"status_code":401}}}',
    )

    try:
        source.find(RecognizedTrack(title="Song", artist="Artist"))
    except ValueError as error:
        assert str(error) == "Musixmatch API status 401"
    else:
        raise AssertionError("A rejected Musixmatch response must not look like no lyrics.")
