"""Small standard-library HTTP adapters for external-service boundaries."""

import ssl
import time
from collections.abc import Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import certifi


def trusted_ssl_context() -> ssl.SSLContext:
    """Use certifi's CA bundle when Python lacks the operating-system roots."""
    return ssl.create_default_context(cafile=certifi.where())


def get_bytes(url: str, timeout: float = 10.0) -> bytes:
    """Fetch bytes while identifying MusicScope to remote services."""
    request = Request(
        url,
        headers={"User-Agent": "MusicScope/0.1 (https://github.com/louisteron/MusicScope)"},
    )
    return _open_request(request, timeout)


def post_bytes(
    url: str,
    content: bytes,
    headers: Mapping[str, str],
    timeout: float = 10.0,
) -> bytes:
    """POST bytes and return the complete response body."""
    request = Request(url, data=content, headers=dict(headers), method="POST")
    return _open_request(request, timeout)


def _open_request(request: Request, timeout: float) -> bytes:
    """Read a request, retrying only service-side rate-limit or outage responses."""
    for attempt in range(2):
        try:
            with urlopen(request, timeout=timeout, context=trusted_ssl_context()) as response:  # noqa: S310
                return response.read()
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 1:
                raise
            time.sleep(1.0)
    raise RuntimeError("unreachable")
