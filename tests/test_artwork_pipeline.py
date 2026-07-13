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
