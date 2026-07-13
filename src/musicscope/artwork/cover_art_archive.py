"""Cover Art Archive source adapter."""

import json
from collections.abc import Callable
from typing import Any

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes

HttpGet = Callable[[str], bytes]


class CoverArtArchiveSource:
    """Resolve an official Cover Art Archive front-cover URL for a track."""

    _BASE_URL = "https://coverartarchive.org/release"

    def __init__(self, get: HttpGet = get_bytes) -> None:
        self._get = get

    def artwork_url(self, track: RecognizedTrack) -> str | None:
        """Return the preferred 500px front cover when the release is known."""
        if track.musicbrainz_release_id is None:
            return None
        response: dict[str, Any] = json.loads(
            self._get(f"{self._BASE_URL}/{track.musicbrainz_release_id}").decode("utf-8")
        )
        images = response.get("images", [])
        front = next((image for image in images if image.get("front")), None)
        if not isinstance(front, dict):
            return None
        thumbnails = front.get("thumbnails", {})
        return thumbnails.get("500") or front.get("image")
