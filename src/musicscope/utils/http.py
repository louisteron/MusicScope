"""Small standard-library HTTP adapters for external-service boundaries."""

from collections.abc import Mapping
from urllib.request import Request, urlopen


def get_bytes(url: str, timeout: float = 10.0) -> bytes:
    """Fetch bytes while identifying MusicScope to remote services."""
    request = Request(url, headers={"User-Agent": "MusicScope/0.1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()


def post_bytes(
    url: str,
    content: bytes,
    headers: Mapping[str, str],
    timeout: float = 10.0,
) -> bytes:
    """POST bytes and return the complete response body."""
    request = Request(url, data=content, headers=dict(headers), method="POST")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()
