"""ACRCloud adapter for the provider-neutral recognition boundary."""

import base64
import hashlib
import hmac
import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from uuid import uuid4

from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.utils.http import post_bytes

HttpPost = Callable[[str, bytes, Mapping[str, str]], bytes]


@dataclass(frozen=True, slots=True)
class AcrCloudCredentials:
    """ACRCloud credentials loaded from the process environment."""

    host: str
    access_key: str
    access_secret: str

    @classmethod
    def from_environment(cls) -> "AcrCloudCredentials":
        """Load required ACRCloud configuration without embedding secrets in code."""
        names = (
            "MUSICSCOPE_ACRCLOUD_HOST",
            "MUSICSCOPE_ACRCLOUD_ACCESS_KEY",
            "MUSICSCOPE_ACRCLOUD_ACCESS_SECRET",
        )
        values = {name: os.getenv(name) for name in names}
        missing = [name for name, value in values.items() if not value]
        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            raise RuntimeError(msg)
        return cls(
            host=values["MUSICSCOPE_ACRCLOUD_HOST"] or "",
            access_key=values["MUSICSCOPE_ACRCLOUD_ACCESS_KEY"] or "",
            access_secret=values["MUSICSCOPE_ACRCLOUD_ACCESS_SECRET"] or "",
        )


class AcrCloudProvider:
    """Identify audio with ACRCloud's signed Identification API."""

    _ENDPOINT = "/v1/identify"

    def __init__(
        self,
        credentials: AcrCloudCredentials,
        post: HttpPost = post_bytes,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._credentials = credentials
        self._post = post
        self._clock = clock

    def identify(self, clip: AudioClip) -> RecognizedTrack | None:
        """Submit an audio clip and map a successful response to domain metadata."""
        timestamp = str(int(self._clock()))
        signature = self._signature(timestamp)
        fields = {
            "access_key": self._credentials.access_key,
            "sample_bytes": str(len(clip.content)),
            "timestamp": timestamp,
            "signature": signature,
            "data_type": "audio",
            "signature_version": "1",
        }
        body, content_type = self._multipart(fields, clip)
        url = f"https://{self._credentials.host}{self._ENDPOINT}"
        response = json.loads(self._post(url, body, {"Content-Type": content_type}).decode("utf-8"))
        return self._to_track(response)

    def _signature(self, timestamp: str) -> str:
        source = "\n".join(
            ("POST", self._ENDPOINT, self._credentials.access_key, "audio", "1", timestamp)
        )
        digest = hmac.new(
            self._credentials.access_secret.encode("ascii"),
            source.encode("ascii"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("ascii")

    def _multipart(self, fields: Mapping[str, str], clip: AudioClip) -> tuple[bytes, str]:
        boundary = f"----MusicScope{uuid4().hex}"
        parts: list[bytes] = []
        for name, value in fields.items():
            disposition = f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            parts.extend((f"--{boundary}\r\n".encode(), disposition, value.encode(), b"\r\n"))
        parts.extend(
            (
                f"--{boundary}\r\n".encode(),
                b'Content-Disposition: form-data; name="sample"; filename="sample.wav"\r\n',
                f"Content-Type: {clip.content_type}\r\n\r\n".encode(),
                clip.content,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            )
        )
        return b"".join(parts), f"multipart/form-data; boundary={boundary}"

    def _to_track(self, response: Mapping[str, object]) -> RecognizedTrack | None:
        status = response.get("status")
        metadata = response.get("metadata")
        if (
            not isinstance(status, Mapping)
            or status.get("code") != 0
            or not isinstance(metadata, Mapping)
        ):
            return None
        music = metadata.get("music")
        if not isinstance(music, list) or not music or not isinstance(music[0], Mapping):
            return None
        match = music[0]
        title = match.get("title")
        if not isinstance(title, str):
            return None
        artists = match.get("artists")
        names = (
            [entry.get("name") for entry in artists if isinstance(entry, Mapping)]
            if isinstance(artists, list)
            else []
        )
        artist = ", ".join(name for name in names if isinstance(name, str)) or "Unknown artist"
        album_data = match.get("album")
        album = album_data.get("name") if isinstance(album_data, Mapping) else None
        provider_artwork = (
            self._artwork_url(album_data) if isinstance(album_data, Mapping) else None
        )
        external = match.get("external_metadata")
        release_id = self._release_id(external) if isinstance(external, Mapping) else None
        return RecognizedTrack(
            title=title,
            artist=artist,
            album=album if isinstance(album, str) else None,
            musicbrainz_release_id=release_id,
            provider_artwork_url=provider_artwork,
        )

    def _artwork_url(self, album: Mapping[str, object]) -> str | None:
        for key in ("cover", "cover_url"):
            value = album.get(key)
            if isinstance(value, str):
                return value
        return None

    def _release_id(self, external: Mapping[str, object]) -> str | None:
        musicbrainz = external.get("musicbrainz")
        if not isinstance(musicbrainz, Mapping):
            return None
        for key in ("release", "releases"):
            candidate = musicbrainz.get(key)
            if isinstance(candidate, str):
                return candidate
            if isinstance(candidate, list) and candidate and isinstance(candidate[0], Mapping):
                identifier = candidate[0].get("id")
                if isinstance(identifier, str):
                    return identifier
        return None
