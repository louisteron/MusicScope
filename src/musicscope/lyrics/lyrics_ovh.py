"""Unauthenticated Lyrics.ovh fallback for plain, non-synchronized lyrics."""

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes


class LyricsOvhSource:
    """Retrieve plain lyric text and assign a conservative display cadence."""

    _ENDPOINT = "https://api.lyrics.ovh/v1"
    _SUGGEST_ENDPOINT = "https://api.lyrics.ovh/suggest"

    def __init__(self, get: Callable[[str], bytes] = get_bytes) -> None:
        self._get = get

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        """Return plain lyric lines with approximate timestamps when available."""
        payload = self._lyrics_payload(track.artist, track.title)
        content = payload.get("lyrics") if isinstance(payload, dict) else None
        if not isinstance(content, str):
            match = self._suggest_exact_match(track)
            if match is not None:
                payload = self._lyrics_payload(*match)
                content = payload.get("lyrics") if isinstance(payload, dict) else None
        if not isinstance(content, str):
            return ()
        lines = tuple(line.strip() for line in content.splitlines() if line.strip())
        return tuple((index * 4.0, line) for index, line in enumerate(lines))

    def _lyrics_payload(self, artist: str, title: str) -> dict[str, Any]:
        """Retrieve one Lyrics.ovh response, treating a missing entry as empty."""
        try:
            response = self._get(
                f"{self._ENDPOINT}/{quote(artist, safe='')}/{quote(title, safe='')}"
            )
        except HTTPError as error:
            if error.code == 404:
                return {}
            raise
        payload = json.loads(response.decode())
        return payload if isinstance(payload, dict) else {}

    def _suggest_exact_match(self, track: RecognizedTrack) -> tuple[str, str] | None:
        """Find only an exact title/artist candidate before requesting its lyrics."""
        query = quote(f"{track.artist} {track.title}", safe="")
        try:
            payload = json.loads(self._get(f"{self._SUGGEST_ENDPOINT}/{query}").decode())
        except HTTPError:
            return None
        candidates = payload.get("data") if isinstance(payload, dict) else None
        for candidate in candidates if isinstance(candidates, list) else []:
            artist = candidate.get("artist") if isinstance(candidate, dict) else None
            title = candidate.get("title") if isinstance(candidate, dict) else None
            name = artist.get("name") if isinstance(artist, dict) else None
            if (
                isinstance(name, str)
                and isinstance(title, str)
                and name.casefold() == track.artist.casefold()
                and title.casefold() == track.title.casefold()
            ):
                return name, title
        return None
