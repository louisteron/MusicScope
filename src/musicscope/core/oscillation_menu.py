"""Menu state for runtime oscilloscope adjustments."""

from collections.abc import Callable

from musicscope.audio.output import AudioOutputDevice
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.config import RecognitionMode
from musicscope.core.recognition_settings import RecognitionSettings
from musicscope.renderer.color_settings import ColorSettings
from musicscope.renderer.oscillation_settings import OscillationSettings
from musicscope.renderer.track_info_settings import TrackInfoSettings


class OscillationMenu:
    """Manage selection and formatting for the oscilloscope settings overlay."""

    _SETTINGS = (
        "Amplitude",
        "Thickness",
        "Response",
        "Color Mode",
        "Phosphor Color",
        "Track Number",
        "Lyrics Wave",
        "Text Wave",
        "Lyric Entry",
        "Audio Output",
        "Recognition",
    )

    def __init__(
        self,
        settings: OscillationSettings,
        color_settings: ColorSettings,
        track_info_settings: TrackInfoSettings | None = None,
        output_settings: AudioOutputSettings | None = None,
        on_output_change: Callable[[AudioOutputDevice | None], None] | None = None,
        recognition_settings: RecognitionSettings | None = None,
        on_recognition_change: Callable[[RecognitionMode], None] | None = None,
    ) -> None:
        self._settings = settings
        self._color_settings = color_settings
        self._track_info_settings = track_info_settings or TrackInfoSettings()
        self._output_settings = output_settings or AudioOutputSettings(())
        self._on_output_change = on_output_change
        self._recognition_settings = recognition_settings or RecognitionSettings(
            RecognitionMode.OFF
        )
        self._on_recognition_change = on_recognition_change
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
        if setting == "Phosphor Color":
            self._color_settings.cycle_phosphor_color(direction)
            return
        if setting == "Track Number":
            self._track_info_settings.toggle_track_number()
            return
        if setting == "Lyrics Wave":
            self._track_info_settings.toggle_lyrics_wave()
            return
        if setting == "Text Wave":
            self._track_info_settings.toggle_lyrics_reactive()
            return
        if setting == "Lyric Entry":
            self._track_info_settings.cycle_lyric_entry_effect(direction)
            return
        if setting == "Audio Output":
            self._output_settings.cycle(direction)
            if self._on_output_change is not None:
                self._on_output_change(self._output_settings.selected_device)
            return
        if setting == "Recognition":
            self._recognition_settings.cycle_mode(direction)
            if self._on_recognition_change is not None:
                self._on_recognition_change(self._recognition_settings.mode)
            return
        self._settings.adjust(setting, direction)

    def lines(self) -> tuple[str, ...]:
        """Return the display-ready menu lines."""
        values = (
            f"AMPLITUDE  {self._settings.amplitude:.2f}",
            f"THICKNESS  {self._settings.thickness:.1f}",
            f"RESPONSE   {self._settings.response:.0f}",
            f"COLOR      {self._color_settings.mode.value}",
            f"PHOSPHOR   {self._color_settings.phosphor_color.value}",
            f"TRACK NO.  {'ON' if self._track_info_settings.show_track_number else 'OFF'}",
            f"LYRICS WAVE  {'ON' if self._track_info_settings.lyrics_wave else 'OFF'}",
            f"TEXT WAVE  {'ON' if self._track_info_settings.lyrics_reactive else 'OFF'}",
            f"LYRIC ENTRY  {self._track_info_settings.lyric_entry_effect.value}",
            f"OUTPUT     {self._output_settings.label}",
            f"RECOG. {self._recognition_settings.label} {self._recognition_settings.status}",
        )
        return tuple(
            f"{'>' if index == self._selected_index else ' '} {line}"
            for index, line in enumerate(values)
        )

    def columns(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Split visual controls from audio and recognition controls for the overlay."""
        lines = self.lines()
        return lines[:9], lines[9:]
