"""AudD adapter for the provider-neutral recognition boundary."""

import json
import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from uuid import uuid4

from musicscope.recognition.models import AudioClip, RecognizedTrack
from musicscope.utils.http import post_bytes

HttpPost = Callable[[str, bytes, Mapping[str, str]], bytes]


@dataclass(frozen=True, slots=True)
class AudDCredentials:
    """AudD API token loaded from the process environment."""

    api_token: str

    @classmethod
    def from_environment(cls) -> "AudDCredentials":
        """Load the AudD token without embedding a secret in source code."""
        api_token = os.getenv("MUSICSCOPE_AUDD_API_TOKEN")
        if not api_token:
            raise RuntimeError("Missing required environment variable: MUSICSCOPE_AUDD_API_TOKEN")
        return cls(api_token=api_token)


class AudDProvider:
    """Identify short audio clips through AudD's standard recognition API."""

    _ENDPOINT = "https://api.audd.io/"
    _MINIMUM_CONFIDENCE = 70

    def __init__(
        self,
        credentials: AudDCredentials,
        post: HttpPost = post_bytes,
        logger: logging.Logger | None = None,
    ) -> None:
        self._credentials = credentials
        self._post = post
        self._logger = logger or logging.getLogger("musicscope")

    def identify(self, clip: AudioClip) -> RecognizedTrack | None:
        """Submit a clip and map an AudD result to provider-neutral metadata."""
        body, content_type = self._multipart(
            {
                "api_token": self._credentials.api_token,
                "return": "musicbrainz,spotify",
            },
            clip,
        )
        try:
            response = json.loads(
                self._post(self._ENDPOINT, body, {"Content-Type": content_type}).decode("utf-8")
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self._logger.warning("AudD request failed (%s): %s", type(error).__name__, error)
            return None
        return self._to_track(response)

    def _multipart(self, fields: Mapping[str, str], clip: AudioClip) -> tuple[bytes, str]:
        boundary = f"----MusicScope{uuid4().hex}"
        parts: list[bytes] = []
        for name, value in fields.items():
            disposition = f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            parts.extend((f"--{boundary}\r\n".encode(), disposition, value.encode(), b"\r\n"))
        parts.extend(
            (
                f"--{boundary}\r\n".encode(),
                b'Content-Disposition: form-data; name="file"; filename="sample.wav"\r\n',
                f"Content-Type: {clip.content_type}\r\n\r\n".encode(),
                clip.content,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            )
        )
        return b"".join(parts), f"multipart/form-data; boundary={boundary}"

    def _to_track(self, response: Mapping[str, object]) -> RecognizedTrack | None:
        result = response.get("result")
        if response.get("status") != "success":
            message = self._error_message(response)
            if message.startswith("Recognition failed"):
                self._logger.info(
                    "AudD could not fingerprint this clip; waiting for the next segment."
                )
            else:
                self._logger.warning("AudD rejected the sample: %s", message)
            return None
        if not isinstance(result, Mapping):
            return None
        if not self._is_confident(result):
            self._logger.info("Ignoring a low-confidence AudD identification.")
            return None
        title = result.get("title")
        artist = result.get("artist")
        if not isinstance(title, str) or not isinstance(artist, str):
            return None
        album = result.get("album")
        musicbrainz = result.get("musicbrainz")
        spotify = result.get("spotify")
        return RecognizedTrack(
            title=title,
            artist=artist,
            album=album if isinstance(album, str) else None,
            musicbrainz_release_id=self._release_id(musicbrainz),
            provider_artwork_url=self._spotify_artwork_url(spotify),
        )

    @classmethod
    def _is_confident(cls, result: Mapping[str, object]) -> bool:
        """Reject only explicit low-confidence matches; older responses remain compatible."""
        score = result.get("score")
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                return True
        if not isinstance(score, (int, float)):
            return True
        threshold = (
            cls._MINIMUM_CONFIDENCE / 100
            if 0.0 <= score <= 1.0
            else cls._MINIMUM_CONFIDENCE
        )
        return score >= threshold

    @staticmethod
    def _error_message(response: Mapping[str, object]) -> str:
        error = response.get("error")
        if isinstance(error, Mapping):
            message = error.get("error_message") or error.get("error_code")
            if isinstance(message, (str, int)):
                return str(message)
        return "unknown response"

    @staticmethod
    def _release_id(musicbrainz: object) -> str | None:
        if not isinstance(musicbrainz, Mapping):
            return None
        release = musicbrainz.get("release")
        if isinstance(release, Mapping):
            identifier = release.get("id")
            return identifier if isinstance(identifier, str) else None
        return release if isinstance(release, str) else None

    @staticmethod
    def _spotify_artwork_url(spotify: object) -> str | None:
        if not isinstance(spotify, Mapping):
            return None
        album = spotify.get("album")
        if not isinstance(album, Mapping):
            return None
        images = album.get("images")
        if not isinstance(images, list) or not images or not isinstance(images[0], Mapping):
            return None
        url = images[0].get("url")
        return url if isinstance(url, str) else None
