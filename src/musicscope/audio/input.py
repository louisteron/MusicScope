"""SoundDevice capture adapter."""

import logging
from collections.abc import Callable

import numpy as np
import sounddevice as sd

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame


class AudioInput:
    """Capture microphone blocks and publish analyzed frames."""

    def __init__(
        self,
        analyzer: AudioAnalyzer,
        on_frame: Callable[[AudioFrame], None],
        sample_rate: int,
        block_size: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._on_frame = on_frame
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._logger = logger or logging.getLogger(__name__)
        self._stream: sd.InputStream | None = None

    @property
    def is_running(self) -> bool:
        """Whether the capture stream has been started."""
        return self._stream is not None and self._stream.active

    def start(self) -> None:
        """Start the default input device."""
        if self._stream is not None:
            return
        self._stream = sd.InputStream(
            channels=1,
            samplerate=self._sample_rate,
            blocksize=self._block_size,
            callback=self._handle_block,
        )
        self._stream.start()

    def stop(self) -> None:
        """Stop and release the capture stream."""
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None

    def _handle_block(
        self,
        indata: np.ndarray,
        _frames: int,
        _time: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            self._logger.warning("Audio input status: %s", status)
        self._on_frame(self._analyzer.analyze(indata))
