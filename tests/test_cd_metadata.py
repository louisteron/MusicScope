"""Tests for local physical-CD metadata lookup."""

import json

from musicscope.recognition.cd import MusicBrainzCdLookup


class FakeDiscReader:
    def read_id(self, device: str | None) -> str:
        assert device == "/dev/sr0"
        return "disc-id"


def test_cd_lookup_resolves_release_metadata_without_audio_fingerprinting() -> None:
    def get(url: str) -> bytes:
        assert "disc-id" in url
        return json.dumps(
            {
                "releases": [
                    {
                        "id": "release-id",
                        "title": "Discovery",
                        "artist-credit": [{"name": "Daft Punk"}],
                        "media": [
                            {
                                "discs": [{"id": "disc-id"}],
                                "tracks": [{"title": "One More Time", "position": 1}],
                            }
                        ],
                    }
                ]
            }
        ).encode()

    release = MusicBrainzCdLookup(reader=FakeDiscReader(), get=get).identify("/dev/sr0")

    assert release is not None
    assert release.disc_id == "disc-id"
    assert release.track.title == "One More Time"
    assert release.track.artist == "Daft Punk"
    assert release.track.track_number == 1
    assert release.track.musicbrainz_release_id == "release-id"


def test_cd_lookup_returns_none_when_the_disc_is_unknown() -> None:
    release = MusicBrainzCdLookup(
        reader=FakeDiscReader(),
        get=lambda _: b'{"releases": []}',
    ).identify("/dev/sr0")

    assert release is None
