"""Tests for the metadata-only cover-art fallback search."""

import json

from musicscope.artwork.musicbrainz_search import MusicBrainzReleaseSearch
from musicscope.recognition.models import RecognizedTrack


def test_search_resolves_a_release_from_title_and_artist() -> None:
    def get(url: str) -> bytes:
        assert "recording" in url
        assert "One+More+Time" in url
        return json.dumps({"recordings": [{"releases": [{"id": "release-id"}]}]}).encode()

    release_id = MusicBrainzReleaseSearch(get).find_release_id(
        RecognizedTrack("One More Time", "Daft Punk")
    )

    assert release_id == "release-id"
