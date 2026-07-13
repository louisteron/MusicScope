"""Pure audio analysis primitives."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class AudioFrame:
    """A compact audio snapshot consumed by a scene."""

    volume: float
    spectrum: tuple[float, ...] = ()


class AudioAnalyzer:
    """Calculate RMS volume and frequency-band levels from audio samples."""

    def __init__(self, bin_count: int = 48) -> None:
        if bin_count <= 0:
            msg = "Bin count must be positive."
            raise ValueError(msg)
        self._bin_count = bin_count

    def analyze(self, samples: NDArray[np.floating]) -> AudioFrame:
        """Return normalized volume and spectral levels for an input block."""
        if samples.size == 0:
            return AudioFrame(volume=0.0, spectrum=(0.0,) * self._bin_count)
        mono = np.mean(samples, axis=1) if samples.ndim > 1 else samples
        rms = float(np.sqrt(np.mean(np.square(mono, dtype=np.float64))))
        windowed = mono * np.hanning(mono.size)
        magnitudes = np.abs(np.fft.rfft(windowed))[1:]
        if magnitudes.size < self._bin_count:
            magnitudes = np.pad(magnitudes, (0, self._bin_count - magnitudes.size))
        bands = np.array_split(magnitudes, self._bin_count)
        levels = tuple(float(np.clip(np.sqrt(np.mean(band)) * 3.0, 0.0, 1.0)) for band in bands)
        return AudioFrame(volume=float(np.clip(rms, 0.0, 1.0)), spectrum=levels)
