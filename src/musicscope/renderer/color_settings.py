"""Runtime color-mode settings shared by visual renderers."""

from dataclasses import dataclass
from enum import StrEnum


class ColorMode(StrEnum):
    """Available phosphor color treatments."""

    NEON_GREEN = "NEON GREEN"
    COVER_NEON = "COVER NEON"
    COVER_THEME = "COVER THEME"


class PhosphorColor(StrEnum):
    """Selectable CRT phosphor palettes for the whole visual environment."""

    GREEN = "GREEN"
    WHITE = "WHITE"
    AMBER = "AMBER"
    BLUE = "BLUE"
    VIOLET = "VIOLET"
    RED = "RED"
    PINK = "PINK"
    YELLOW = "YELLOW"


@dataclass(slots=True)
class ColorSettings:
    """Store the selected treatment, phosphor palette and cover dominant color."""

    mode: ColorMode = ColorMode.COVER_NEON
    phosphor_color: PhosphorColor = PhosphorColor.GREEN
    primary_color: tuple[float, float, float] = (0.10, 1.0, 0.34)

    def cycle_mode(self, direction: int) -> None:
        """Move through the available color modes."""
        modes = tuple(ColorMode)
        self.mode = modes[(modes.index(self.mode) + direction) % len(modes)]

    def cycle_phosphor_color(self, direction: int) -> None:
        """Move through the available environment palettes."""
        colors = tuple(PhosphorColor)
        self.phosphor_color = colors[
            (colors.index(self.phosphor_color) + direction) % len(colors)
        ]

    @property
    def theme_color(self) -> tuple[float, float, float]:
        """Return the color used by the non-cover renderers."""
        if self.mode is ColorMode.COVER_THEME:
            return self.primary_color
        return {
            PhosphorColor.GREEN: (0.10, 1.0, 0.34),
            PhosphorColor.WHITE: (0.92, 1.0, 0.96),
            PhosphorColor.AMBER: (1.0, 0.58, 0.10),
            PhosphorColor.BLUE: (0.18, 0.60, 1.0),
            PhosphorColor.VIOLET: (0.70, 0.32, 1.0),
            PhosphorColor.RED: (1.0, 0.08, 0.12),
            PhosphorColor.PINK: (1.0, 0.12, 0.62),
            PhosphorColor.YELLOW: (1.0, 0.84, 0.08),
        }[self.phosphor_color]
