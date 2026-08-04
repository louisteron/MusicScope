"""Public iTunes catalogue search used as a final artwork-only fallback."""

import json
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlencode

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes

HttpGet = Callable[[str], bytes]


class ItunesArtworkSearch:
    """Find album artwork from a track title and artist without AudD coupling."""

    _ENDPOINT = "https://itunes.apple.com/search"

    def __init__(self, get: HttpGet = get_bytes) -> None:
        self._get = get

    def find_artwork_url(self, track: RecognizedTrack) -> str | None:
        """Return the best available large artwork URL from the public catalogue."""
        results = self._search(f"{track.title} {track.artist}", "song")
        candidates = (
            (self._match_score(track, result), result)
            for result in results
            if isinstance(result, dict)
        )
        for score, result in sorted(candidates, reverse=True, key=lambda candidate: candidate[0]):
            if not self._is_confident_match(track, result, score):
                continue
            url = result.get("artworkUrl100")
            if isinstance(url, str):
                return url.replace("100x100bb", "600x600bb")
        return self._album_artwork_url(track)

    def _album_artwork_url(self, track: RecognizedTrack) -> str | None:
        """Find the album directly when song-level cataloguing differs from AudD."""
        if track.album is None:
            return None
        results = self._search(f"{track.album} {track.artist}", "album")
        for result in results:
            if not isinstance(result, dict):
                continue
            album = result.get("collectionName")
            artist = result.get("artistName")
            if not isinstance(album, str) or not isinstance(artist, str):
                continue
            if self._similarity(track.album, album) < 0.80:
                continue
            if self._similarity(track.artist, artist) < 0.55:
                continue
            url = result.get("artworkUrl100")
            if isinstance(url, str):
                return url.replace("100x100bb", "600x600bb")
        return None

    def _search(self, term: str, entity: str) -> list[object]:
        """Run one public catalogue query and return its raw result entries."""
        parameters = {"term": term, "entity": entity, "limit": 5}
        payload: dict[str, Any] = json.loads(
            self._get(f"{self._ENDPOINT}?{urlencode(parameters)}").decode("utf-8")
        )
        results = payload.get("results", [])
        return results if isinstance(results, list) else []

    @classmethod
    def _is_confident_match(
        cls,
        track: RecognizedTrack,
        result: dict[str, Any],
        score: float,
    ) -> bool:
        """Reject unrelated catalogue results rather than showing a wrong cover."""
        title = result.get("trackName")
        artist = result.get("artistName")
        if not isinstance(title, str) or not isinstance(artist, str):
            return False
        title_score = cls._similarity(track.title, title)
        artist_score = cls._similarity(track.artist, artist)
        return score >= 0.75 and title_score >= 0.80 and artist_score >= 0.55

    @staticmethod
    def _match_score(track: RecognizedTrack, result: dict[str, Any]) -> float:
        title = result.get("trackName")
        artist = result.get("artistName")
        if not isinstance(title, str) or not isinstance(artist, str):
            return 0.0
        title_score = ItunesArtworkSearch._similarity(track.title, title)
        artist_score = ItunesArtworkSearch._similarity(track.artist, artist)
        return title_score * 0.75 + artist_score * 0.25

    @staticmethod
    def _similarity(first: str, second: str) -> float:
        first_normalised = ItunesArtworkSearch._normalise(first)
        second_normalised = ItunesArtworkSearch._normalise(second)
        if not first_normalised or not second_normalised:
            return 0.0
        if first_normalised in second_normalised or second_normalised in first_normalised:
            return 1.0
        return SequenceMatcher(None, first_normalised, second_normalised).ratio()

    @staticmethod
    def _normalise(value: str) -> str:
        return "".join(character for character in value.casefold() if character.isalnum())
