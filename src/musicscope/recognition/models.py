"""Data returned by a music-recognition provider."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AudioClip:
    """An encoded audio clip ready to send to an identification provider."""

    content: bytes
    sample_rate: int
    content_type: str = "audio/wav"


@dataclass(frozen=True, slots=True)
class RecognizedTrack:
    """Provider-neutral metadata for the track currently being played."""

    title: str
    artist: str
    album: str | None = None
    musicbrainz_release_id: str | None = None
    provider_artwork_url: str | None = None
