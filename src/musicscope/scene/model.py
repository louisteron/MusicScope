"""State exchanged between scenes and renderers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualState:
    """The renderer-facing state for the active scene."""

    energy: float = 0.0
    spectrum: tuple[float, ...] = ()
