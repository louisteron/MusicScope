"""Runtime color-mode settings shared by visual renderers."""

from dataclasses import dataclass
from enum import StrEnum


class ColorMode(StrEnum):
    """Available phosphor color treatments."""

    NEON_GREEN = "NEON GREEN"
    COVER_NEON = "COVER NEON"
    COVER_THEME = "COVER THEME"


@dataclass(slots=True)
class ColorSettings:
    """Store the selected treatment and current cover's dominant color."""

    mode: ColorMode = ColorMode.NEON_GREEN
    primary_color: tuple[float, float, float] = (0.10, 1.0, 0.34)

    def cycle_mode(self, direction: int) -> None:
        """Move through the available color modes."""
        modes = tuple(ColorMode)
        self.mode = modes[(modes.index(self.mode) + direction) % len(modes)]

    @property
    def theme_color(self) -> tuple[float, float, float]:
        """Return the color used by the non-cover renderers."""
        return self.primary_color if self.mode is ColorMode.COVER_THEME else (0.10, 1.0, 0.34)
