"""Tests for the ACRCloud provider adapter."""

import json

import pytest

from musicscope.recognition.acrcloud import AcrCloudCredentials, AcrCloudProvider
from musicscope.recognition.models import AudioClip


def test_credentials_are_loaded_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MUSICSCOPE_ACRCLOUD_HOST", "identify.example.test")
    monkeypatch.setenv("MUSICSCOPE_ACRCLOUD_ACCESS_KEY", "key")
    monkeypatch.setenv("MUSICSCOPE_ACRCLOUD_ACCESS_SECRET", "secret")
    assert AcrCloudCredentials.from_environment().access_key == "key"


def test_credentials_reject_missing_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MUSICSCOPE_ACRCLOUD_HOST", raising=False)
    monkeypatch.delenv("MUSICSCOPE_ACRCLOUD_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MUSICSCOPE_ACRCLOUD_ACCESS_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MUSICSCOPE_ACRCLOUD_HOST"):
        AcrCloudCredentials.from_environment()


def test_provider_maps_a_successful_response_to_a_track() -> None:
    response = {
        "status": {"code": 0},
        "metadata": {
            "music": [
                {
                    "title": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album", "cover": "https://covers.example.test/song.jpg"},
                    "external_metadata": {"musicbrainz": {"release": "release-id"}},
                }
            ]
        },
    }
    requests: list[tuple[str, bytes, dict[str, str]]] = []

    def post(url: str, body: bytes, headers: dict[str, str]) -> bytes:
        requests.append((url, body, headers))
        return json.dumps(response).encode()

    provider = AcrCloudProvider(
        AcrCloudCredentials("identify.example.test", "key", "secret"),
        post=post,
        clock=lambda: 1_700_000_000,
    )
    track = provider.identify(AudioClip(content=b"audio", sample_rate=44_100))

    assert track is not None
    assert track.title == "Song"
    assert track.musicbrainz_release_id == "release-id"
    assert track.provider_artwork_url == "https://covers.example.test/song.jpg"
    assert requests[0][0] == "https://identify.example.test/v1/identify"
    assert b'name="sample_bytes"\r\n\r\n5' in requests[0][1]


def test_provider_returns_none_for_a_non_match() -> None:
    provider = AcrCloudProvider(
        AcrCloudCredentials("host", "key", "secret"),
        post=lambda *_: b'{"status": {"code": 1001}}',
    )
    assert provider.identify(AudioClip(content=b"audio", sample_rate=44_100)) is None
