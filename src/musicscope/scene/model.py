"""State exchanged between scenes and renderers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualState:
    """The renderer-facing state for the active scene."""

    energy: float = 0.0
    bass_energy: float = 0.0
    spectrum: tuple[float, ...] = ()
    waveform: tuple[float, ...] = ()
    track_title: str | None = None
    artist_name: str | None = None
    artwork_path: str | None = None
