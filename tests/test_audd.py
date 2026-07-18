"""Tests for the AudD recognition provider."""

import logging
from urllib.error import URLError

import pytest

from musicscope.recognition.audd import AudDCredentials, AudDProvider
from musicscope.recognition.models import AudioClip


def test_credentials_are_loaded_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MUSICSCOPE_AUDD_API_TOKEN", "token")

    assert AudDCredentials.from_environment().api_token == "token"


def test_credentials_reject_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MUSICSCOPE_AUDD_API_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="MUSICSCOPE_AUDD_API_TOKEN"):
        AudDCredentials.from_environment()


def test_provider_maps_a_successful_response() -> None:
    def post(_url: str, body: bytes, headers: dict[str, str]) -> bytes:
        assert b'name="api_token"' in body
        assert b"token" in body
        assert b'name="file"' in body
        assert headers["Content-Type"].startswith("multipart/form-data")
        return b'''{
            "status": "success",
            "result": {
                "artist": "Daft Punk",
                "title": "One More Time",
                "album": "Discovery",
                "musicbrainz": {"release": {"id": "release-id"}},
                "spotify": {"album": {"images": [{"url": "https://cover.test/image.jpg"}]}}
            }
        }'''

    provider = AudDProvider(AudDCredentials("token"), post=post)
    track = provider.identify(AudioClip(content=b"wav", sample_rate=44_100))

    assert track is not None
    assert track.artist == "Daft Punk"
    assert track.title == "One More Time"
    assert track.musicbrainz_release_id == "release-id"
    assert track.provider_artwork_url == "https://cover.test/image.jpg"


def test_provider_returns_none_for_a_no_match() -> None:
    provider = AudDProvider(
        AudDCredentials("token"),
        post=lambda _url, _body, _headers: b'{"status": "success", "result": null}',
    )

    assert provider.identify(AudioClip(content=b"wav", sample_rate=44_100)) is None


def test_provider_logs_a_network_failure(caplog: pytest.LogCaptureFixture) -> None:
    provider = AudDProvider(
        AudDCredentials("token"),
        post=lambda _url, _body, _headers: (_ for _ in ()).throw(URLError("offline")),
    )

    assert provider.identify(AudioClip(content=b"wav", sample_rate=44_100)) is None
    assert "URLError" in caplog.text
    assert "offline" in caplog.text


def test_provider_treats_fingerprint_failure_as_a_recoverable_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("test.audd")
    provider = AudDProvider(
        AudDCredentials("token"),
        post=lambda _url, _body, _headers: b'''{
            "status": "error",
            "error": {"error_message": "Recognition failed: no fingerprint"}
        }''',
        logger=logger,
    )

    caplog.set_level(logging.INFO, logger="test.audd")
    assert provider.identify(AudioClip(content=b"wav", sample_rate=44_100)) is None
    assert "could not fingerprint" in caplog.text
