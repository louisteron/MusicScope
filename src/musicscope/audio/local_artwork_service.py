"""Background cover lookup for the currently playing local playlist track."""

import logging
from collections.abc import Callable
from threading import Lock, Thread

from musicscope.artwork import ArtworkPipeline
from musicscope.audio.local_playlist import LocalPlaylist


class LocalArtworkService:
    """Prefer a file's own cover, then resolve and cache an online album cover."""

    def __init__(
        self,
        playlist: LocalPlaylist,
        artwork_pipeline: ArtworkPipeline,
        on_artwork: Callable[[int, str | None], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self._playlist = playlist
        self._artwork_pipeline = artwork_pipeline
        self._on_artwork = on_artwork
        self._logger = logger or logging.getLogger("musicscope")
        self._lock = Lock()
        self._request_id = 0

    def load(self, one_based_index: int) -> None:
        """Resolve artwork without blocking the renderer or mpv monitor."""
        with self._lock:
            self._request_id += 1
            request_id = self._request_id
        Thread(
            target=self._resolve,
            args=(one_based_index, request_id),
            name="local-artwork",
            daemon=True,
        ).start()

    def cancel(self) -> None:
        """Discard the result of any lookup still running in the background."""
        with self._lock:
            self._request_id += 1

    def _resolve(self, one_based_index: int, request_id: int) -> None:
        item = self._playlist.item_at(one_based_index)
        if item is None:
            return
        artwork_path = item.artwork_path
        if artwork_path is None:
            artwork = self._artwork_pipeline.resolve(item.track)
            artwork_path = artwork.path if artwork is not None else None
        with self._lock:
            if request_id != self._request_id:
                return
        self._on_artwork(one_based_index, str(artwork_path) if artwork_path is not None else None)
        if artwork_path is not None:
            self._logger.info("Local playlist cover ready: %s", artwork_path)
