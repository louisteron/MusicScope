"""Provider-neutral contracts and fallback composition for timed lyrics."""

import logging
from collections.abc import Iterable
from typing import Protocol

from musicscope.recognition.models import RecognizedTrack


class TimedLyricsSource(Protocol):
    """Retrieve timestamped lyric lines for one identified track."""

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]: ...


class FallbackLyricsSource:
    """Try lyric providers in order until one returns synchronized lines."""

    def __init__(
        self,
        sources: Iterable[TimedLyricsSource],
        logger: logging.Logger | None = None,
    ) -> None:
        self._sources = tuple(sources)
        self._logger = logger or logging.getLogger("musicscope")

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        """Return the first successful timed-lyrics result."""
        for source in self._sources:
            try:
                lines = source.find(track)
            except (OSError, ValueError) as error:
                self._logger.info(
                    "%s lyrics lookup unavailable: %s",
                    self._provider_name(source),
                    error,
                )
                continue
            if lines:
                self._logger.info("Timed lyrics loaded from %s.", self._provider_name(source))
                return lines
            self._logger.info("%s returned no timed lyrics.", self._provider_name(source))
        return ()

    @staticmethod
    def _provider_name(source: TimedLyricsSource) -> str:
        return source.__class__.__name__.removesuffix("LyricsSource")
