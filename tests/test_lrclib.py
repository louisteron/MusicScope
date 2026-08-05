"""Tests for LRCLIB lyric matching."""

from musicscope.lyrics.lrclib import LrclibLyricsSource
from musicscope.recognition.models import RecognizedTrack


def test_lrclib_can_search_by_title_when_local_file_has_no_artist() -> None:
    requested: list[str] = []

    def get(url: str) -> bytes:
        requested.append(url)
        return b'[{"trackName":"Song","artistName":"Known Artist","syncedLyrics":"[00:01.00]Line"}]'

    lines = LrclibLyricsSource(get=get).find(RecognizedTrack("Song", "Local file"))

    assert lines == ((1.0, "Line"),)
    assert requested == ["https://lrclib.net/api/search?track_name=Song"]
