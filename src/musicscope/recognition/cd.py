"""Local physical-CD metadata lookup through MusicBrainz Disc IDs."""

import json
import os
import plistlib
import sys
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
        self._configure_macos_library_path()
        try:
            import discid
        except ImportError as error:
            raise CdMetadataUnavailable("python-discid/libdiscid is not installed") from error
        except OSError as error:
            raise CdMetadataUnavailable(f"libdiscid could not be loaded: {error}") from error
        try:
            disc = discid.read(device) if device else discid.read()
        except Exception as error:  # libdiscid exposes platform-specific errors.
            if sys.platform == "darwin":
                disc = self._read_macos_toc(discid)
                if disc is not None:
                    return str(disc.id)
            raise CdMetadataUnavailable(f"no readable audio CD was found: {error}") from error
        return str(disc.id)

    @staticmethod
    def _configure_macos_library_path() -> None:
        """Make Homebrew's non-system libdiscid discoverable to Python on macOS."""
        if sys.platform != "darwin":
            return
        candidates = (
            "/opt/homebrew/opt/libdiscid/lib",
            "/usr/local/opt/libdiscid/lib",
        )
        directory = next((path for path in candidates if os.path.isdir(path)), None)
        if directory is None:
            return
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        directories = existing.split(":") if existing else []
        if directory not in directories:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join((directory, *directories))

    @staticmethod
    def _read_macos_toc(discid_module: object) -> object | None:
        """Build a Disc ID from the CDDA table macOS exposes in its mounted volume."""
        for volume in sorted(os.scandir("/Volumes"), key=lambda entry: entry.name):
            toc_path = os.path.join(volume.path, ".TOC.plist")
            if not os.path.isfile(toc_path):
                continue
            try:
                with open(toc_path, "rb") as toc_file:
                    payload = plistlib.load(toc_file)
                session = payload["Sessions"][0]
                tracks = session["Track Array"]
                offsets = [track["Start Block"] for track in tracks if not track["Data"]]
                return discid_module.put(
                    session["First Track"],
                    session["Last Track"],
                    session["Leadout Block"],
                    offsets,
                )
            except (KeyError, OSError, TypeError, ValueError):
                continue
        return None


@dataclass(frozen=True, slots=True)
class CdRelease:
    """A MusicBrainz release resolved from the CD currently in the drive."""

    disc_id: str
    track: RecognizedTrack
    tracks: tuple[RecognizedTrack, ...] = ()


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
        url = f"{self._BASE_URL}/{quote(disc_id, safe='')}?fmt=json&inc=artist-credits+recordings"
        payload: dict[str, Any] = json.loads(self._get(url).decode("utf-8"))
        releases = payload.get("releases", [])
        if not releases or not isinstance(releases[0], dict):
            return None
        release = releases[0]
        release_id = release.get("id")
        title = release.get("title")
        if not isinstance(release_id, str) or not isinstance(title, str):
            return None
        song = self._first_track(release, disc_id)
        artist = self._artist_name(song) or self._artist_name(release) or "Unknown artist"
        tracks = self._tracks(release, disc_id, title, artist, release_id)
        initial_track = tracks[0] if tracks else RecognizedTrack(
            title=self._track_title(song) or title,
            artist=artist,
            album=title,
            track_number=self._track_number(song),
            musicbrainz_release_id=release_id,
        )
        return CdRelease(
            disc_id=disc_id,
            track=initial_track,
            tracks=tracks,
        )

    @staticmethod
    def _first_track(release: dict[str, Any], disc_id: str) -> dict[str, Any] | None:
        """Return the first track on the medium matching the inserted disc."""
        media = release.get("media", [])
        for medium in media if isinstance(media, list) else []:
            if not isinstance(medium, dict):
                continue
            discs = medium.get("discs", [])
            if not isinstance(discs, list):
                continue
            has_disc = any(
                isinstance(disc, dict) and disc.get("id") == disc_id
                for disc in discs
            )
            tracks = medium.get("tracks", [])
            if has_disc and isinstance(tracks, list) and tracks and isinstance(tracks[0], dict):
                return tracks[0]
        return None

    @staticmethod
    def _track_title(track: dict[str, Any] | None) -> str | None:
        if track is None:
            return None
        title = track.get("title")
        return title if isinstance(title, str) else None

    @staticmethod
    def _track_number(track: dict[str, Any] | None) -> int | None:
        if track is None:
            return None
        position = track.get("position")
        return position if isinstance(position, int) and position > 0 else None

    @classmethod
    def _tracks(
        cls,
        release: dict[str, Any],
        disc_id: str,
        album: str,
        release_artist: str,
        release_id: str,
    ) -> tuple[RecognizedTrack, ...]:
        """Map the inserted medium's ordered MusicBrainz tracks to neutral metadata."""
        media = release.get("media", [])
        for medium in media if isinstance(media, list) else []:
            if not isinstance(medium, dict):
                continue
            discs = medium.get("discs", [])
            tracks = medium.get("tracks", [])
            if not isinstance(discs, list) or not isinstance(tracks, list):
                continue
            if not any(isinstance(disc, dict) and disc.get("id") == disc_id for disc in discs):
                continue
            return tuple(
                RecognizedTrack(
                    title=cls._track_title(track) or album,
                    artist=cls._artist_name(track) or release_artist,
                    album=album,
                    track_number=cls._track_number(track),
                    musicbrainz_release_id=release_id,
                )
                for track in tracks
                if isinstance(track, dict)
            )
        return ()

    @staticmethod
    def _artist_name(release: dict[str, Any] | None) -> str:
        if release is None:
            return ""
        credit = release.get("artist-credit", [])
        names = [part.get("name") for part in credit if isinstance(part, dict)]
        return "".join(name for name in names if isinstance(name, str))
