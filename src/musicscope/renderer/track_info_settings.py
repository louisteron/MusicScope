"""User settings for the currently playing track label."""

from dataclasses import dataclass
from enum import StrEnum


class LyricEntryEffect(StrEnum):
    """Visual transition used when a new synchronized lyric begins."""

    FADE = "FADE"
    MORPH = "MORPH"
    NO_FADE = "NO FADE"


@dataclass(slots=True)
class TrackInfoSettings:
    """Own optional details displayed alongside track metadata."""

    show_track_number: bool = False
    lyrics_wave: bool = True
    lyric_entry_effect: LyricEntryEffect = LyricEntryEffect.NO_FADE
    lyrics_reactive: bool = True

    def toggle_track_number(self) -> None:
        """Show or hide the current album track number."""
        self.show_track_number = not self.show_track_number

    def toggle_lyrics_wave(self) -> None:
        """Switch between the conventional scope and the lyric-led visual."""
        self.lyrics_wave = not self.lyrics_wave

    def cycle_lyric_entry_effect(self, direction: int) -> None:
        """Select fade-in text or oscilloscope-to-letter morphing."""
        effects = tuple(LyricEntryEffect)
        index = effects.index(self.lyric_entry_effect)
        self.lyric_entry_effect = effects[(index + direction) % len(effects)]

    def toggle_lyrics_reactive(self) -> None:
        """Enable or disable bass-driven distortion of the lyric glyphs."""
        self.lyrics_reactive = not self.lyrics_reactive
