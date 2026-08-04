"""Selection state for MusicScope's audio monitoring output."""

from dataclasses import dataclass

from musicscope.audio.output import AudioOutputDevice


@dataclass(slots=True)
class AudioOutputSettings:
    """Store the output selected from the on-screen settings menu."""

    devices: tuple[AudioOutputDevice, ...]
    selected_index: int = -1

    @property
    def selected_device(self) -> AudioOutputDevice | None:
        """Return the selected device, or ``None`` when monitoring is off."""
        return self.devices[self.selected_index] if self.selected_index >= 0 else None

    @property
    def label(self) -> str:
        """Return a compact display label for the menu."""
        if self.selected_device is None:
            return "OFF"
        return self.selected_device.name[:22].upper()

    def cycle(self, direction: int) -> None:
        """Select the previous or next output; ``OFF`` is part of the cycle."""
        choices = len(self.devices) + 1
        self.selected_index = (self.selected_index + direction + 1) % choices - 1

    def select_speakers(self) -> AudioOutputDevice | None:
        """Select integrated speakers, falling back to the first physical output."""
        speaker_markers = ("haut-parleurs", "speakers", "speaker", "built-in")
        loopback_markers = ("blackhole", "loopback", "soundflower", "vb-cable", "cable output")
        index = next(
            (
                position
                for position, device in enumerate(self.devices)
                if any(marker in device.name.casefold() for marker in speaker_markers)
            ),
            None,
        )
        if index is None:
            index = next(
                (
                    position
                    for position, device in enumerate(self.devices)
                    if not any(marker in device.name.casefold() for marker in loopback_markers)
                ),
                None,
            )
        self.selected_index = index if index is not None else -1
        return self.selected_device
