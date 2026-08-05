"""Asynchronous lyric lookup service."""

import logging
from collections.abc import Callable
from threading import Lock, Thread

from musicscope.lyrics.source import LyricsSource
from musicscope.recognition.models import RecognizedTrack

LyricsReadyCallback = Callable[[tuple[tuple[float, str], ...]], None]


class LyricsService:
    """Fetch lyrics away from playback and rendering threads."""

    def __init__(
        self,
        source: LyricsSource,
        on_lyrics: Callable[[tuple[tuple[float, str], ...]], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self._source = source
        self._on_lyrics = on_lyrics
        self._logger = logger or logging.getLogger("musicscope")
        self._lock = Lock()
        self._request_id = 0

    def load(
        self,
        track: RecognizedTrack,
        on_ready: LyricsReadyCallback | None = None,
    ) -> None:
        """Load lyrics and notify when the lookup has conclusively completed."""
        with self._lock:
            self._request_id += 1
            request_id = self._request_id
        self._on_lyrics(())
        Thread(target=self._fetch, args=(track, request_id, on_ready), daemon=True).start()

    def cancel(self) -> None:
        """Discard any lyric lookup still running for a previous playback source."""
        with self._lock:
            self._request_id += 1

    def _fetch(
        self,
        track: RecognizedTrack,
        request_id: int,
        on_ready: LyricsReadyCallback | None,
    ) -> None:
        try:
            lines = self._source.find(track)
        except (OSError, ValueError):
            self._logger.info("No timed lyrics available for %s — %s.", track.artist, track.title)
            lines = ()
        with self._lock:
            if request_id != self._request_id:
                return
        self._on_lyrics(lines)
        if on_ready is not None:
            on_ready(lines)
