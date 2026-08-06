"""WASAPI loopback capture for the default Windows speaker."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from threading import Event, Thread
from typing import Protocol

import numpy as np

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame


class LoopbackRecorder(Protocol):
    """Read normalized audio frames from a Windows output-loopback source."""

    def record(self, numframes: int) -> np.ndarray: ...


LoopbackRecorderFactory = Callable[[int, int, int], AbstractContextManager[LoopbackRecorder]]


class WindowsLoopbackInput:
    """Publish analysis frames from the default Windows speaker through WASAPI."""

    def __init__(
        self,
        analyzer: AudioAnalyzer,
        on_frame: Callable[[AudioFrame], None],
        sample_rate: int,
        block_size: int,
        on_samples: Callable[[np.ndarray], None] | None = None,
        recorder_factory: LoopbackRecorderFactory | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._on_frame = on_frame
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._on_samples = on_samples
        self._recorder_factory = recorder_factory or self._default_recorder
        self._logger = logger or logging.getLogger(__name__)
        self._stopped = Event()
        self._thread: Thread | None = None

    @property
    def is_running(self) -> bool:
        """Whether the background loopback reader is active."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start reading the default speaker without using the microphone."""
        if self._thread is not None:
            return
        self._stopped.clear()
        self._thread = Thread(target=self._run, name="windows-loopback", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Request the reader to finish after its current audio block."""
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        try:
            with self._recorder_factory(self._sample_rate, 2, self._block_size) as recorder:
                while not self._stopped.is_set():
                    self._publish(recorder.record(numframes=self._block_size))
        except Exception as error:
            self._logger.warning("Windows system-audio loopback unavailable: %s", error)

    def _publish(self, samples: np.ndarray) -> None:
        normalized = np.asarray(samples, dtype=np.float32)
        self._on_frame(self._analyzer.analyze(normalized))
        if self._on_samples is not None:
            self._on_samples(normalized)

    @staticmethod
    def _default_recorder(
        sample_rate: int, channels: int, block_size: int
    ) -> AbstractContextManager[LoopbackRecorder]:
        """Open the WASAPI loopback associated with the default Windows speaker."""
        import soundcard as sound_card

        speaker = sound_card.default_speaker()
        loopback = sound_card.get_microphone(str(speaker.name), include_loopback=True)
        if loopback is None:
            raise RuntimeError("no loopback source for the default Windows speaker")
        return loopback.recorder(
            samplerate=sample_rate,
            channels=channels,
            blocksize=block_size,
        )
