"""Local physical-CD metadata lookup through MusicBrainz Disc IDs."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

from musicscope.recognition.models import RecognizedTrack
from musicscope.utils.http import get_bytes


class CdMetadataUnavailable(RuntimeError):
    """Raised when no readable optical drive or Disc ID support is available."""


class DiscReader(Protocol):
    """Read the stable MusicBrainz Disc ID from a physical audio CD."""

    def read_id(self, device: str | None) -> str: ...


class LibDiscIdReader:
    """Adapter for libdiscid, imported lazily so AudD users need no CD hardware."""

    def read_id(self, device: str | None) -> str:
        try:
            import discid
        except ImportError as error:
            raise CdMetadataUnavailable("python-discid/libdiscid is not installed") from error
        try:
            disc = discid.read(device) if device else discid.read()
        except Exception as error:  # libdiscid exposes platform-specific errors.
            raise CdMetadataUnavailable("no readable audio CD was found") from error
        return str(disc.id)


@dataclass(frozen=True, slots=True)
class CdRelease:
    """A MusicBrainz release resolved from the CD currently in the drive."""

    disc_id: str
    track: RecognizedTrack


HttpGet = Callable[[str], bytes]


class MusicBrainzCdLookup:
    """Resolve CD metadata without sending audio to a fingerprinting provider."""

    _BASE_URL = "https://musicbrainz.org/ws/2/discid"

    def __init__(self, reader: DiscReader | None = None, get: HttpGet = get_bytes) -> None:
        self._reader = reader or LibDiscIdReader()
        self._get = get

    def identify(self, device: str | None = None) -> CdRelease | None:
        """Return album metadata for the inserted disc, if MusicBrainz knows it."""
        disc_id = self._reader.read_id(device)
        url = f"{self._BASE_URL}/{quote(disc_id, safe='')}?fmt=json&inc=artist-credits"
        payload: dict[str, Any] = json.loads(self._get(url).decode("utf-8"))
        releases = payload.get("releases", [])
        if not releases or not isinstance(releases[0], dict):
            return None
        release = releases[0]
        release_id = release.get("id")
        title = release.get("title")
        if not isinstance(release_id, str) or not isinstance(title, str):
            return None
        artist = self._artist_name(release)
        return CdRelease(
            disc_id=disc_id,
            track=RecognizedTrack(
                title=title,
                artist=artist,
                album=title,
                musicbrainz_release_id=release_id,
            ),
        )

    @staticmethod
    def _artist_name(release: dict[str, Any]) -> str:
        credit = release.get("artist-credit", [])
        names = [part.get("name") for part in credit if isinstance(part, dict)]
        return "".join(name for name in names if isinstance(name, str)) or "Unknown artist"
