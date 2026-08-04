"""Tests for artwork source resolution and local cache behavior."""

import json

from musicscope.artwork.cache import ArtworkCache
from musicscope.artwork.cover_art_archive import CoverArtArchiveSource
from musicscope.artwork.pipeline import ArtworkPipeline
from musicscope.recognition.models import RecognizedTrack


def test_pipeline_downloads_then_reuses_cached_cover(tmp_path) -> None:
    cover_url = "https://covers.example.test/cover.jpg"
    calls: list[str] = []

    def get(url: str) -> bytes:
        calls.append(url)
        if url.endswith("release-id"):
            response = {"images": [{"front": True, "thumbnails": {"500": cover_url}}]}
            return json.dumps(response).encode()
        return b"image-data"

    pipeline = ArtworkPipeline(CoverArtArchiveSource(get), ArtworkCache(tmp_path), get)
    track = RecognizedTrack("Song", "Artist", musicbrainz_release_id="release-id")

    first = pipeline.resolve(track)
    second = pipeline.resolve(track)

    assert first is not None and second is not None
    assert first.path.read_bytes() == b"image-data"
    assert first.path == second.path
    assert calls.count(cover_url) == 1


def test_pipeline_skips_cover_art_archive_without_a_release_id(tmp_path) -> None:
    pipeline = ArtworkPipeline(CoverArtArchiveSource(lambda _: b""), ArtworkCache(tmp_path))
    assert pipeline.resolve(RecognizedTrack("Song", "Artist")) is None


def test_pipeline_searches_musicbrainz_when_audd_has_no_cover(tmp_path) -> None:
    cover_url = "https://covers.example.test/searched-cover.jpg"

    def get(url: str) -> bytes:
        if "recording" in url:
            return json.dumps({"recordings": [{"releases": [{"id": "searched-release"}]}]}).encode()
        if url.endswith("searched-release"):
            return json.dumps(
                {"images": [{"front": True, "thumbnails": {"500": cover_url}}]}
            ).encode()
        return b"searched-image"

    pipeline = ArtworkPipeline(CoverArtArchiveSource(get), ArtworkCache(tmp_path), get)

    artwork = pipeline.resolve(RecognizedTrack("Song", "Artist"))

    assert artwork is not None
    assert artwork.source_url == cover_url
    assert artwork.path.read_bytes() == b"searched-image"


def test_pipeline_falls_back_to_provider_artwork_when_archive_is_unavailable(tmp_path) -> None:
    provider_url = "https://provider.example.test/cover.jpg"

    def get(url: str) -> bytes:
        if "coverartarchive" in url:
            raise OSError("archive unavailable")
        return b"provider-cover"

    pipeline = ArtworkPipeline(CoverArtArchiveSource(get), ArtworkCache(tmp_path), get)
    track = RecognizedTrack(
        "Song",
        "Artist",
        musicbrainz_release_id="release-id",
        provider_artwork_url=provider_url,
    )

    artwork = pipeline.resolve(track)

    assert artwork is not None
    assert artwork.source_url == provider_url
    assert artwork.path.read_bytes() == b"provider-cover"


def test_pipeline_searches_when_provider_cover_cannot_be_downloaded(tmp_path) -> None:
    searched_url = "https://covers.example.test/recovered-cover.jpg"

    def get(url: str) -> bytes:
        if url == "https://provider.example.test/missing.jpg":
            raise OSError("provider unavailable")
        if "recording" in url:
            return json.dumps({"recordings": [{"releases": [{"id": "searched-release"}]}]}).encode()
        if url.endswith("searched-release"):
            return json.dumps(
                {"images": [{"front": True, "thumbnails": {"500": searched_url}}]}
            ).encode()
        return b"searched-image"

    pipeline = ArtworkPipeline(CoverArtArchiveSource(get), ArtworkCache(tmp_path), get)
    track = RecognizedTrack(
        "Song",
        "Artist",
        provider_artwork_url="https://provider.example.test/missing.jpg",
    )

    artwork = pipeline.resolve(track)

    assert artwork is not None
    assert artwork.source_url == searched_url
