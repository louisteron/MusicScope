"""Audio monitoring output for routing captured music to a Hi-Fi system."""

import logging
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from queue import Empty, Full, Queue
from typing import Any

import numpy as np
import sounddevice as sd

DeviceQuery = Callable[[], Sequence[Mapping[str, Any]]]
DefaultDeviceQuery = Callable[[], Any]


@dataclass(frozen=True, slots=True)
class AudioOutputDevice:
    """An audio endpoint that can receive MusicScope's monitored signal."""

    name: str
    channels: int


class AudioOutputDeviceSelector:
    """List playback devices without making platform-specific jack assumptions."""

    def __init__(
        self,
        query_devices: DeviceQuery = sd.query_devices,
        default_device: DefaultDeviceQuery = lambda: sd.default.device,
    ) -> None:
        self._query_devices = query_devices
        self._default_device = default_device

    def available(self) -> tuple[AudioOutputDevice, ...]:
        """Return every usable output, including a connected headphone jack."""
        return tuple(
            AudioOutputDevice(
                name=str(device["name"]),
                channels=min(2, int(device["max_output_channels"])),
            )
            for device in self._query_devices()
            if int(device["max_output_channels"]) > 0
        )

    def default_output(self) -> AudioOutputDevice | None:
        """Return the operating system's selected playback endpoint, if usable."""
        default_device = self._default_device()
        try:
            output_index = int(default_device[1])
            device = self._query_devices()[output_index]
        except (IndexError, KeyError, TypeError, ValueError):
            return None
        if int(device["max_output_channels"]) <= 0:
            return None
        return AudioOutputDevice(
            name=str(device["name"]),
            channels=min(2, int(device["max_output_channels"])),
        )


class AudioOutput:
    """Play captured audio on one selected output with a small non-blocking buffer."""

    _QUEUE_BLOCKS = 24

    def __init__(self, sample_rate: int, block_size: int, logger: logging.Logger) -> None:
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._logger = logger
        self._channels = 2
        self._queue: Queue[np.ndarray] = Queue(maxsize=self._QUEUE_BLOCKS)
        self._pending = np.empty((0, self._channels), dtype="f4")
        self._stream: sd.OutputStream | None = None

    def select(self, device: AudioOutputDevice | None) -> None:
        """Switch monitoring to *device*, or turn it off when the value is ``None``."""
        self.stop()
        if device is None:
            self._logger.info("Audio monitoring output disabled.")
            return
        self._channels = device.channels
        self._pending = np.empty((0, self._channels), dtype="f4")
        try:
            self._stream = sd.OutputStream(
                device=device.name,
                channels=self._channels,
                samplerate=self._sample_rate,
                blocksize=self._block_size,
                callback=self._play_block,
            )
            self._stream.start()
        except sd.PortAudioError as error:
            self._stream = None
            self._logger.warning("Could not open audio output %s: %s", device.name, error)
            return
        self._logger.info("Routing captured audio to: %s", device.name)

    def push(self, samples: np.ndarray) -> None:
        """Queue a captured block for playback without blocking the input callback."""
        if self._stream is None:
            return
        block = self._match_channels(samples)
        try:
            self._queue.put_nowait(block)
        except Full:
            with suppress(Empty):
                self._queue.get_nowait()
            with suppress(Full):
                self._queue.put_nowait(block)

    def stop(self) -> None:
        """Stop the active output stream and discard buffered audio."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._clear_queue()

    def _play_block(
        self,
        outdata: np.ndarray,
        frames: int,
        _time: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            self._logger.warning("Audio output status: %s", status)
        outdata.fill(0.0)
        written = 0
        while written < frames:
            if not len(self._pending):
                try:
                    self._pending = self._queue.get_nowait()
                except Empty:
                    break
            count = min(frames - written, len(self._pending))
            outdata[written : written + count] = self._pending[:count]
            self._pending = self._pending[count:]
            written += count

    def _match_channels(self, samples: np.ndarray) -> np.ndarray:
        block = np.asarray(samples, dtype="f4")
        if block.ndim == 1:
            block = block[:, None]
        if block.shape[1] == self._channels:
            return block.copy()
        if block.shape[1] == 1:
            return np.repeat(block, self._channels, axis=1)
        return block[:, : self._channels].copy()

    def _clear_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except Empty:
                return
