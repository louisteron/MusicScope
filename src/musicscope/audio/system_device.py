"""Selection of virtual devices that carry system-output audio."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import sounddevice as sd

DeviceQuery = Callable[[], Sequence[Mapping[str, Any]]]


@dataclass(frozen=True, slots=True)
class SystemAudioDevice:
    """An input device known to receive the operating system's audio output."""

    name: str
    channels: int
    sample_rate: int


class SystemAudioDeviceSelector:
    """Find an installed virtual loopback input without selecting a microphone."""

    _LOOPBACK_NAMES = ("blackhole", "loopback", "soundflower", "vb-cable", "cable output")

    def __init__(self, query_devices: DeviceQuery = sd.query_devices) -> None:
        self._query_devices = query_devices

    def select(self, requested_name: str | None = None) -> SystemAudioDevice | None:
        """Return a requested loopback device or the first known virtual device."""
        devices = self._query_devices()
        for device in devices:
            name = str(device["name"])
            is_requested = (
                requested_name is not None and requested_name.casefold() in name.casefold()
            )
            is_loopback = any(marker in name.casefold() for marker in self._LOOPBACK_NAMES)
            if (is_requested or is_loopback) and int(device["max_input_channels"]) > 0:
                return SystemAudioDevice(
                    name=name,
                    channels=min(2, int(device["max_input_channels"])),
                    sample_rate=int(device["default_samplerate"]),
                )
        return None
