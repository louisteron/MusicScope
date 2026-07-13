"""Artwork domain data."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Artwork:
    """A cached artwork file usable by a future visual-contour pipeline."""

    path: Path
    source_url: str
