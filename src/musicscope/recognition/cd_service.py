"""Background service for local CD metadata identification."""

import logging
from collections.abc import Callable
from threading import Event, Thread
from urllib.error import HTTPError

from musicscope.artwork.pipeline import ArtworkPipeline
from musicscope.recognition.cd import CdMetadataUnavailable, MusicBrainzCdLookup
from musicscope.recognition.workflow import IdentificationResult


class CdMetadataService:
    """Poll an optical drive and publish a new album only when its disc changes."""

    def __init__(
        self,
        lookup: MusicBrainzCdLookup,
        artwork_pipeline: ArtworkPipeline,
        on_identification: Callable[[IdentificationResult], None],
        device: str | None = None,
        poll_seconds: float = 20.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._lookup = lookup
        self._artwork_pipeline = artwork_pipeline
        self._on_identification = on_identification
        self._device = device
        self._poll_seconds = poll_seconds
        self._logger = logger or logging.getLogger("musicscope")
        self._stopped = Event()
        self._thread: Thread | None = None
        self._last_disc_id: str | None = None

    def start(self) -> None:
        """Start optical-drive polling away from the rendering thread."""
        if self._thread is None:
            self._thread = Thread(target=self._run, name="cd-metadata", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Request service shutdown."""
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        while not self._stopped.is_set():
            try:
                release = self._lookup.identify(self._device)
            except CdMetadataUnavailable as error:
                self._logger.info("Local CD metadata waiting: %s", error)
            except HTTPError as error:
                self._logger.warning(
                    "Local CD metadata lookup failed (HTTP %s): %s", error.code, error.reason
                )
            except (OSError, ValueError) as error:
                self._logger.warning("Local CD metadata lookup failed: %s", type(error).__name__)
            else:
                if release is not None and release.disc_id != self._last_disc_id:
                    self._last_disc_id = release.disc_id
                    artwork = self._artwork_pipeline.resolve(release.track)
                    self._on_identification(
                        IdentificationResult(release.track, artwork, album_tracks=release.tracks)
                    )
                    self._logger.info("Local CD identified: %s", release.track.title)
            self._stopped.wait(self._poll_seconds)
