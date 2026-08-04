"""Artwork retrieval and local caching, independent of recognition providers."""

from musicscope.artwork.deezer_search import DeezerArtworkSearch
from musicscope.artwork.itunes_search import ItunesArtworkSearch
from musicscope.artwork.musicbrainz_search import MusicBrainzReleaseSearch
from musicscope.artwork.pipeline import ArtworkPipeline

__all__ = [
    "ArtworkPipeline",
    "DeezerArtworkSearch",
    "ItunesArtworkSearch",
    "MusicBrainzReleaseSearch",
]
