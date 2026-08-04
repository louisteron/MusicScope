"""Tests for HTTPS transport configuration."""

import ssl
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from musicscope.utils.http import _open_request, trusted_ssl_context


def test_http_uses_a_verifying_ssl_context() -> None:
    context = trusted_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname


def test_http_retries_a_temporary_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def open_request(*_args: object, **_kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise HTTPError("https://example.test", 503, "Service Unavailable", {}, None)

        class Response:
            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self) -> bytes:
                return b"ok"

        return Response()

    monkeypatch.setattr("musicscope.utils.http.urlopen", open_request)
    monkeypatch.setattr("musicscope.utils.http.time.sleep", lambda _: None)

    assert _open_request(Request("https://example.test"), 1.0) == b"ok"
    assert attempts == 2
