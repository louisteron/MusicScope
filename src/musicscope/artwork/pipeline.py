"""Artwork acquisition use case, decoupled from recognition implementations."""

from collections.abc import Callable
from pathlib import Path

from musicscope.artwork.cache import ArtworkCache
from musicscope.artwork.cover_art_archive import CoverArtArchiveSource
from musicscope.artwork.models import Artwork
from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes

HttpGet = Callable[[str], bytes]


class ArtworkPipeline:
    """Resolve, download and cache artwork independently from track recognition."""

    def __init__(
        self,
        source: CoverArtArchiveSource,
        cache: ArtworkCache,
        get: HttpGet = get_bytes,
    ) -> None:
        self._source = source
        self._cache = cache
        self._get = get

    @classmethod
    def with_cache_directory(
        cls,
        source: CoverArtArchiveSource,
        get: HttpGet,
        directory: Path,
    ) -> "ArtworkPipeline":
        """Build a pipeline with a caller-selected local cache directory."""
        return cls(source=source, cache=ArtworkCache(directory), get=get)

    @classmethod
    def default(cls) -> "ArtworkPipeline":
        """Build the production pipeline with its conventional local cache."""
        return cls(source=CoverArtArchiveSource(), cache=ArtworkCache.default())

    def resolve(self, track: RecognizedTrack) -> Artwork | None:
        """Return a cached Cover Art Archive image for an identified release."""
        url = self._source.artwork_url(track) or track.provider_artwork_url
        if url is None:
            return None
        cached = self._cache.load(url)
        path = cached or self._cache.store(url, self._get(url))
        return Artwork(path=path, source_url=url)
