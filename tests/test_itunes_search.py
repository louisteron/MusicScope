"""Tests for the final public-catalogue artwork fallback."""

import json

from musicscope.artwork.itunes_search import ItunesArtworkSearch
from musicscope.recognition.models import RecognizedTrack


def test_itunes_search_returns_a_larger_matching_cover() -> None:
    def get(_url: str) -> bytes:
        return json.dumps(
            {
                "results": [
                    {
                        "trackName": "One More Time",
                        "artistName": "Daft Punk",
                        "artworkUrl100": "https://example.test/100x100bb.jpg",
                    }
                ]
            }
        ).encode()

    url = ItunesArtworkSearch(get).find_artwork_url(RecognizedTrack("One More Time", "Daft Punk"))

    assert url == "https://example.test/600x600bb.jpg"


def test_itunes_search_tolerates_different_featured_artist_formatting() -> None:
    def get(_url: str) -> bytes:
        return json.dumps(
            {
                "results": [
                    {
                        "trackName": "Save Your Tears (Remix)",
                        "artistName": "The Weeknd & Ariana Grande",
                        "artworkUrl100": "https://example.test/100x100bb.jpg",
                    }
                ]
            }
        ).encode()

    url = ItunesArtworkSearch(get).find_artwork_url(
        RecognizedTrack("Save Your Tears Remix", "The Weeknd feat. Ariana Grande")
    )

    assert url == "https://example.test/600x600bb.jpg"


def test_itunes_search_rejects_an_unrelated_catalogue_result() -> None:
    def get(_url: str) -> bytes:
        return json.dumps(
            {
                "results": [
                    {
                        "trackName": "Song (2011 Remaster)",
                        "artistName": "An Artist",
                        "artworkUrl100": "https://example.test/100x100bb.jpg",
                    }
                ]
            }
        ).encode()

    url = ItunesArtworkSearch(get).find_artwork_url(RecognizedTrack("A Different Song", "Artist"))

    assert url is None


def test_itunes_search_uses_the_album_when_the_song_result_does_not_match() -> None:
    calls = 0

    def get(_url: str) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            return b'{"results": []}'
        return json.dumps(
            {
                "results": [
                    {
                        "collectionName": "Discovery",
                        "artistName": "Daft Punk",
                        "artworkUrl100": "https://example.test/100x100bb.jpg",
                    }
                ]
            }
        ).encode()

    url = ItunesArtworkSearch(get).find_artwork_url(
        RecognizedTrack("One More Time", "Daft Punk", album="Discovery")
    )

    assert url == "https://example.test/600x600bb.jpg"
