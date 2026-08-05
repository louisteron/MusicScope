"""Provider-neutral contracts and fallback composition for lyric sources."""

import logging
from collections.abc import Iterable
from typing import Protocol

from musicscope.recognition.models import RecognizedTrack


class LyricsSource(Protocol):
    """Retrieve display-ready lyric lines for one identified track."""

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]: ...


class FallbackLyricsSource:
    """Try lyric sources in order until one returns displayable lines."""

    def __init__(
        self,
        sources: Iterable[LyricsSource],
        logger: logging.Logger | None = None,
    ) -> None:
        self._sources = tuple(sources)
        self._logger = logger or logging.getLogger("musicscope")

    def find(self, track: RecognizedTrack) -> tuple[tuple[float, str], ...]:
        """Return the first source result, preserving provider order."""
        for source in self._sources:
            try:
                lines = source.find(track)
            except (OSError, ValueError) as error:
                self._logger.info(
                    "%s lyric lookup unavailable: %s", self._source_name(source), error
                )
                continue
            if lines:
                self._logger.info("Lyrics loaded from %s.", self._source_name(source))
                return lines
            self._logger.info("%s returned no lyrics.", self._source_name(source))
        return ()

    @staticmethod
    def _source_name(source: LyricsSource) -> str:
        return source.__class__.__name__.removesuffix("Source")
