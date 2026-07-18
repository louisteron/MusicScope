"""Mutable runtime settings for the oscilloscope trace."""

from dataclasses import dataclass


@dataclass(slots=True)
class OscillationSettings:
    """Own the user-adjustable parameters of the waveform renderer."""

    amplitude: float = 0.48
    thickness: float = 1.0
    response: float = 32.0

    def adjust(self, setting: str, direction: int) -> None:
        """Adjust one setting by a bounded, user-visible increment."""
        if setting == "Amplitude":
            self.amplitude = min(0.85, max(0.15, self.amplitude + direction * 0.04))
        elif setting == "Thickness":
            self.thickness = min(2.0, max(0.5, self.thickness + direction * 0.1))
        elif setting == "Response":
            self.response = min(60.0, max(8.0, self.response + direction * 4.0))
        else:
            raise ValueError(f"Unknown oscillation setting: {setting}")
