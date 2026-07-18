"""Menu state for runtime oscilloscope adjustments."""

from musicscope.renderer.color_settings import ColorSettings
from musicscope.renderer.oscillation_settings import OscillationSettings


class OscillationMenu:
    """Manage selection and formatting for the oscilloscope settings overlay."""

    _SETTINGS = ("Amplitude", "Thickness", "Response", "Color Mode")

    def __init__(self, settings: OscillationSettings, color_settings: ColorSettings) -> None:
        self._settings = settings
        self._color_settings = color_settings
        self._visible = False
        self._selected_index = 0

    @property
    def visible(self) -> bool:
        """Whether the overlay should be rendered."""
        return self._visible

    def toggle(self) -> None:
        """Show or hide the menu."""
        self._visible = not self._visible

    def move_selection(self, direction: int) -> None:
        """Move selection through the available settings."""
        self._selected_index = (self._selected_index + direction) % len(self._SETTINGS)

    def adjust_selected(self, direction: int) -> None:
        """Apply a horizontal adjustment to the selected setting."""
        setting = self._SETTINGS[self._selected_index]
        if setting == "Color Mode":
            self._color_settings.cycle_mode(direction)
            return
        self._settings.adjust(setting, direction)

    def lines(self) -> tuple[str, ...]:
        """Return the display-ready menu lines."""
        values = (
            f"AMPLITUDE  {self._settings.amplitude:.2f}",
            f"THICKNESS  {self._settings.thickness:.1f}",
            f"RESPONSE   {self._settings.response:.0f}",
            f"COLOR      {self._color_settings.mode.value}",
        )
        return tuple(
            f"{'>' if index == self._selected_index else ' '} {line}"
            for index, line in enumerate(values)
        )
