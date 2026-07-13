"""Asynchronous bridge from microphone blocks to the identification workflow."""

import queue
from collections.abc import Callable
from contextlib import suppress
from threading import Event, Thread

import numpy as np

from musicscope.audio.wav import encode_wav
from musicscope.recognition.models import AudioClip
from musicscope.recognition.workflow import IdentificationResult, IdentificationWorkflow


class RecognitionService:
    """Collect audio off the callback thread and identify fixed-duration clips."""

    def __init__(
        self,
        workflow: IdentificationWorkflow,
        sample_rate: int,
        on_identification: Callable[[IdentificationResult], None],
        clip_seconds: int = 10,
    ) -> None:
        self._workflow = workflow
        self._sample_rate = sample_rate
        self._on_identification = on_identification
        self._clip_size = sample_rate * clip_seconds
        self._samples: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=128)
        self._stopped = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start the worker before microphone capture starts."""
        if self._thread is not None:
            return
        self._thread = Thread(target=self._run, name="music-recognition", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the worker without blocking the audio callback."""
        self._stopped.set()
        with suppress(queue.Full):
            self._samples.put_nowait(None)
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def submit_samples(self, samples: np.ndarray) -> None:
        """Copy a capture block into the bounded worker queue."""
        try:
            self._samples.put_nowait(np.asarray(samples, dtype=np.float32).copy())
        except queue.Full:
            return

    def _run(self) -> None:
        chunks: list[np.ndarray] = []
        count = 0
        while not self._stopped.is_set():
            block = self._samples.get()
            if block is None:
                return
            chunks.append(block.reshape(-1))
            count += block.size
            if count < self._clip_size:
                continue
            samples = np.concatenate(chunks)[: self._clip_size]
            chunks = []
            count = 0
            clip = AudioClip(
                content=encode_wav(samples, self._sample_rate),
                sample_rate=self._sample_rate,
            )
            result = self._workflow.identify(clip)
            if result is not None:
                self._on_identification(result)
