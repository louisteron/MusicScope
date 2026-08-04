"""Official Musixmatch synchronized-lyrics adapter."""

import json
import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from musicscope.lyrics.lrc import parse_lrc
from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes


class MusixmatchLyricsSource:
    """Fetch LRC subtitles from Musixmatch with a user-supplied API key."""

    _ENDPOINT = "https://api.musixmatch.com/ws/1.1/matcher.subtitle.get"

    def __init__(self, api_key: str, get: Callable[[str], bytes] = get_bytes) -> None:
        self._api_key = api_key
        self._get = get

    @classmethod
    def from_environment(
        cls,
        get: Callable[[str], bytes] = get_bytes,
    ) -> "MusixmatchLyricsSource | None":
        """Build the optional provider only when its credential is configured."""
        api_key = os.getenv("MUSICSCOPE_MUSIXMATCH_API_KEY", "").strip()
        return cls(api_key, get) if api_key else None

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        """Find an exact track's LRC subtitle, or no lines when unavailable."""
        query = urlencode(
            {
                "apikey": self._api_key,
                "q_track": track.title,
                "q_artist": track.artist,
                "subtitle_format": "lrc",
            }
        )
        payload: dict[str, Any] = json.loads(self._get(f"{self._ENDPOINT}?{query}").decode())
        message = payload.get("message") if isinstance(payload, dict) else None
        header = message.get("header") if isinstance(message, dict) else None
        status = header.get("status_code") if isinstance(header, dict) else None
        if isinstance(status, int) and status != 200:
            msg = f"Musixmatch API status {status}"
            raise ValueError(msg)
        body = message.get("body") if isinstance(message, dict) else None
        subtitle = body.get("subtitle") if isinstance(body, dict) else None
        content = subtitle.get("subtitle_body") if isinstance(subtitle, dict) else None
        return parse_lrc(content) if isinstance(content, str) else ()
