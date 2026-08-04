"""MusicBrainz lookup used only when a recognized track has no cover metadata."""

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes

HttpGet = Callable[[str], bytes]


class MusicBrainzReleaseSearch:
    """Find a release ID from a track title and artist without using a recognition provider."""

    _BASE_URL = "https://musicbrainz.org/ws/2/recording/"

    def __init__(self, get: HttpGet = get_bytes) -> None:
        self._get = get

    def find_release_id(self, track: RecognizedTrack) -> str | None:
        """Return the best available MusicBrainz release ID for a recognized song."""
        query = f'recording:"{self._escape(track.title)}" AND artist:"{self._escape(track.artist)}"'
        parameters = {"query": query, "fmt": "json", "limit": 5, "inc": "releases"}
        url = f"{self._BASE_URL}?{urlencode(parameters)}"
        payload: dict[str, Any] = json.loads(self._get(url).decode("utf-8"))
        recordings = payload.get("recordings", [])
        if not isinstance(recordings, list):
            return None
        for recording in recordings:
            if not isinstance(recording, dict):
                continue
            release_id = self._release_id(recording)
            if release_id is not None:
                return release_id
        return None

    @staticmethod
    def _release_id(recording: dict[str, Any]) -> str | None:
        releases = recording.get("releases", [])
        if not isinstance(releases, list):
            return None
        for release in releases:
            if isinstance(release, dict) and isinstance(release.get("id"), str):
                return release["id"]
        return None

    @staticmethod
    def _escape(value: str) -> str:
        """Escape the limited Lucene syntax used by MusicBrainz search queries."""
        return value.replace("\\", "\\\\").replace('"', '\\"')
