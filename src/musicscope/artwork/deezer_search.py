"""Public Deezer catalogue search used when other artwork sources have no cover."""

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes

HttpGet = Callable[[str], bytes]


class DeezerArtworkSearch:
    """Resolve an album-cover URL from a strictly matching title and artist."""

    _ENDPOINT = "https://api.deezer.com/search"

    def __init__(self, get: HttpGet = get_bytes) -> None:
        self._get = get

    def find_artwork_url(self, track: RecognizedTrack) -> str | None:
        """Return a large album cover only for a matching Deezer track result."""
        query = f'track:"{track.title}" artist:"{track.artist}"'
        payload: dict[str, Any] = json.loads(
            self._get(f"{self._ENDPOINT}?{urlencode({'q': query})}").decode("utf-8")
        )
        results = payload.get("data", [])
        if not isinstance(results, list):
            return None
        for result in results:
            if not isinstance(result, dict) or not self._matches(track, result):
                continue
            album = result.get("album")
            if not isinstance(album, dict):
                continue
            cover = album.get("cover_xl") or album.get("cover_big")
            return cover if isinstance(cover, str) else None
        return None

    @staticmethod
    def _matches(track: RecognizedTrack, result: dict[str, Any]) -> bool:
        title = result.get("title")
        artist = result.get("artist")
        artist_name = artist.get("name") if isinstance(artist, dict) else None
        return (
            isinstance(title, str)
            and isinstance(artist_name, str)
            and DeezerArtworkSearch._normalise(track.title) == DeezerArtworkSearch._normalise(title)
            and DeezerArtworkSearch._normalise(track.artist)
            == DeezerArtworkSearch._normalise(artist_name)
        )

    @staticmethod
    def _normalise(value: str) -> str:
        return "".join(character for character in value.casefold() if character.isalnum())
