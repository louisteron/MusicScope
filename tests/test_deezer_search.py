"""Tests for the final Deezer artwork fallback."""

import json

from musicscope.artwork.deezer_search import DeezerArtworkSearch
from musicscope.recognition.models import RecognizedTrack


def test_deezer_search_returns_the_matching_album_cover() -> None:
    def get(_url: str) -> bytes:
        return json.dumps(
            {
                "data": [
                    {
                        "title": "Fever",
                        "artist": {"name": "Buckshot"},
                        "album": {"cover_xl": "https://covers.example.test/fever.jpg"},
                    }
                ]
            }
        ).encode()

    url = DeezerArtworkSearch(get).find_artwork_url(RecognizedTrack("Fever", "Buckshot"))

    assert url == "https://covers.example.test/fever.jpg"
