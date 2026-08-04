"""Asynchronous bridge from audio blocks to the identification workflow."""

import logging
import queue
import time
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
        clip_seconds: int = 8,
        minimum_rms: float = 0.0001,
        request_cooldown_seconds: float = 10.0,
        clock: Callable[[], float] = time.monotonic,
        logger: logging.Logger | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self._workflow = workflow
        self._sample_rate = sample_rate
        self._on_identification = on_identification
        self._clip_size = sample_rate * clip_seconds
        self._clip_seconds = clip_seconds
        self._minimum_rms = minimum_rms
        self._request_cooldown_seconds = request_cooldown_seconds
        self._clock = clock
        self._samples: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=128)
        self._stopped = Event()
        self._thread: Thread | None = None
        self._logger = logger or logging.getLogger("musicscope")
        self._on_status = on_status
        self._next_request_at = 0.0

    def start(self) -> None:
        """Start the worker before audio capture starts."""
        if self._thread is not None:
            return
        self._logger.info(
            "AudD waits for audible audio: %s-second clips at most every %s seconds.",
            self._clip_seconds,
            self._request_cooldown_seconds,
        )
        self._set_status("LISTEN")
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
            block = np.asarray(samples, dtype=np.float32)
            mono = block.mean(axis=1) if block.ndim == 2 else block
            self._samples.put_nowait(mono.copy())
        except queue.Full:
            return

    def _run(self) -> None:
        chunks: list[np.ndarray] = []
        count = 0
        while not self._stopped.is_set():
            block = self._samples.get()
            if block is None:
                return
            if not chunks and not self._should_collect(block):
                continue
            if not chunks:
                self._logger.info("Audible signal detected; collecting an AudD sample.")
                self._set_status("COLLECT")
            chunks.append(block.reshape(-1))
            count += block.size
            if count < self._clip_size:
                continue
            samples = np.concatenate(chunks)[: self._clip_size]
            chunks = []
            count = 0
            if not self._has_audible_signal(samples):
                self._logger.info("Skipping quiet audio clip before AudD identification.")
                continue
            clip = AudioClip(
                content=encode_wav(self._normalise_clip(samples), self._sample_rate),
                sample_rate=self._sample_rate,
            )
            self._logger.info("Sending audio clip to AudD for identification.")
            self._set_status("SEARCH")
            self._next_request_at = self._clock() + self._request_cooldown_seconds
            try:
                result = self._workflow.identify(clip)
            except (OSError, ValueError) as error:
                self._logger.warning("Recognition workflow failed: %s", type(error).__name__)
                self._set_status("ERROR")
                continue
            if result is not None:
                self._on_identification(result)
                self._set_status("FOUND")
            else:
                self._logger.info("AudD did not identify a track in this clip.")
                self._set_status("NO MATCH")

    def _has_audible_signal(self, samples: np.ndarray) -> bool:
        """Avoid spending an AudD request on silence from the system loopback."""
        rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))
        return rms >= self._minimum_rms

    @staticmethod
    def _normalise_clip(samples: np.ndarray) -> np.ndarray:
        """Raise a quiet loopback signal to a fingerprint-friendly level without clipping."""
        audio = np.asarray(samples, dtype=np.float32)
        rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if rms == 0.0 or peak == 0.0:
            return audio
        gain = min(0.12 / rms, 0.95 / peak, 1_000.0)
        return audio * gain

    def _should_collect(self, samples: np.ndarray) -> bool:
        """Collect only audible blocks and respect the request cooldown without needing silence."""
        return self._has_audible_signal(samples) and self._clock() >= self._next_request_at

    def _set_status(self, status: str) -> None:
        """Notify the UI without coupling this worker to GLFW or the renderer."""
        if self._on_status is not None:
            self._on_status(status)
