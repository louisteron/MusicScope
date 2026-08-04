"""Artwork acquisition use case, decoupled from recognition implementations."""

import logging
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from musicscope.artwork.cache import ArtworkCache
from musicscope.artwork.cover_art_archive import CoverArtArchiveSource
from musicscope.artwork.deezer_search import DeezerArtworkSearch
from musicscope.artwork.itunes_search import ItunesArtworkSearch
from musicscope.artwork.models import Artwork
from musicscope.artwork.musicbrainz_search import MusicBrainzReleaseSearch
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
        release_search: MusicBrainzReleaseSearch | None = None,
        internet_search: ItunesArtworkSearch | None = None,
        deezer_search: DeezerArtworkSearch | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._source = source
        self._cache = cache
        self._get = get
        self._release_search = release_search or MusicBrainzReleaseSearch(get)
        self._internet_search = internet_search or ItunesArtworkSearch(get)
        self._deezer_search = deezer_search or DeezerArtworkSearch(get)
        self._searched_urls: dict[tuple[str, str], str] = {}
        self._internet_urls: dict[tuple[str, str], str] = {}
        self._deezer_urls: dict[tuple[str, str], str] = {}
        self._logger = logger or logging.getLogger("musicscope")

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
        """Return cached artwork, preferring Cover Art Archive when available."""
        archive_url = self._archive_url(track)
        for url in (archive_url, track.provider_artwork_url):
            if url is None:
                continue
            artwork = self._download_or_load(url)
            if artwork is not None:
                self._logger.info("Artwork resolved for %s — %s.", track.artist, track.title)
                return artwork
        searched_url = self._searched_archive_url(track)
        if searched_url is not None:
            artwork = self._download_or_load(searched_url)
            if artwork is not None:
                self._logger.info(
                    "Artwork found through MusicBrainz search: %s — %s.",
                    track.artist,
                    track.title,
                )
                return artwork
        internet_url = self._internet_artwork_url(track)
        if internet_url is not None:
            artwork = self._download_or_load(internet_url)
            if artwork is not None:
                self._logger.info(
                    "Artwork found through internet search: %s — %s.",
                    track.artist,
                    track.title,
                )
                return artwork
        deezer_url = self._deezer_artwork_url(track)
        if deezer_url is not None:
            artwork = self._download_or_load(deezer_url)
            if artwork is not None:
                self._logger.info(
                    "Artwork found through Deezer search: %s — %s.",
                    track.artist,
                    track.title,
                )
                return artwork
        self._logger.info("No artwork found for %s — %s.", track.artist, track.title)
        return None

    def _download_or_load(self, url: str) -> Artwork | None:
        """Load a cached image or make one safe download attempt."""
        cached = self._cache.load(url)
        if cached is not None:
            return Artwork(path=cached, source_url=url)
        try:
            path = self._cache.store(url, self._get(url))
        except OSError as error:
            self._logger.info("Artwork download failed from %s: %s", url, type(error).__name__)
            return None
        return Artwork(path=path, source_url=url)

    def _archive_url(self, track: RecognizedTrack) -> str | None:
        """Look up a cover from a release ID already returned by the provider."""
        try:
            return self._source.artwork_url(track)
        except (OSError, ValueError):
            return None

    def _searched_archive_url(self, track: RecognizedTrack) -> str | None:
        """Find a release by title and artist, then query its official cover archive."""
        key = (track.title.casefold(), track.artist.casefold())
        if cached_url := self._searched_urls.get(key):
            return cached_url
        try:
            release_id = self._release_search.find_release_id(track)
            if release_id is None:
                return None
            url = self._source.artwork_url(replace(track, musicbrainz_release_id=release_id))
        except (OSError, ValueError):
            return None
        if url is not None:
            self._searched_urls[key] = url
        return url

    def _internet_artwork_url(self, track: RecognizedTrack) -> str | None:
        """Use a broad public catalogue only after official cover sources failed."""
        key = (track.title.casefold(), track.artist.casefold())
        if cached_url := self._internet_urls.get(key):
            return cached_url
        try:
            url = self._internet_search.find_artwork_url(track)
        except (OSError, ValueError):
            return None
        if url is not None:
            self._internet_urls[key] = url
        return url

    def _deezer_artwork_url(self, track: RecognizedTrack) -> str | None:
        """Use Deezer only after the other artwork catalogues could not help."""
        key = (track.title.casefold(), track.artist.casefold())
        if cached_url := self._deezer_urls.get(key):
            return cached_url
        try:
            url = self._deezer_search.find_artwork_url(track)
        except (OSError, ValueError):
            return None
        if url is not None:
            self._deezer_urls[key] = url
        return url
