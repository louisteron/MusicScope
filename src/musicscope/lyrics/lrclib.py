"""LRCLIB adapter for synchronized lyric lookup."""

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from musicscope.lyrics.lrc import parse_lrc
from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes


class LrclibLyricsSource:
    """Look up timestamped lyrics from LRCLIB using CD track metadata."""

    _ENDPOINT = "https://lrclib.net/api/search"

    def __init__(self, get: Callable[[str], bytes] = get_bytes) -> None:
        self._get = get

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        """Return matched synced lyrics, or no lines when unavailable."""
        parameters = {"track_name": track.title}
        if track.artist.casefold() != "local file":
            parameters["artist_name"] = track.artist
        query = urlencode(parameters)
        payload: list[dict[str, Any]] = json.loads(self._get(f"{self._ENDPOINT}?{query}").decode())
        for result in payload if isinstance(payload, list) else []:
            if not isinstance(result, dict) or not self._matches(track, result):
                continue
            lyrics = result.get("syncedLyrics")
            if isinstance(lyrics, str):
                return parse_lrc(lyrics)
        return ()

    @staticmethod
    def _matches(track: RecognizedTrack, result: dict[str, Any]) -> bool:
        title = result.get("trackName")
        artist = result.get("artistName")
        return (
            isinstance(title, str)
            and isinstance(artist, str)
            and title.casefold() == track.title.casefold()
            and (
                track.artist.casefold() == "local file"
                or artist.casefold() == track.artist.casefold()
            )
        )
