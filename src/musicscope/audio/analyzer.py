"""Pure audio analysis primitives."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class AudioFrame:
    """A compact audio snapshot consumed by a scene."""

    volume: float
    bass_energy: float = 0.0
    spectrum: tuple[float, ...] = ()
    waveform: tuple[float, ...] = ()


class AudioAnalyzer:
    """Calculate RMS volume and frequency-band levels from audio samples."""

    def __init__(
        self,
        bin_count: int = 48,
        waveform_size: int = 512,
        silence_threshold: float = 0.002,
        sample_rate: int = 44_100,
    ) -> None:
        if bin_count <= 0 or waveform_size <= 0 or sample_rate <= 0:
            msg = "Analysis sizes must be positive."
            raise ValueError(msg)
        if silence_threshold < 0:
            msg = "Silence threshold cannot be negative."
            raise ValueError(msg)
        self._bin_count = bin_count
        self._waveform_size = waveform_size
        self._silence_threshold = silence_threshold
        self._sample_rate = sample_rate

    def analyze(self, samples: NDArray[np.floating]) -> AudioFrame:
        """Return normalized volume and spectral levels for an input block."""
        if samples.size == 0:
            return AudioFrame(
                volume=0.0,
                spectrum=(0.0,) * self._bin_count,
                waveform=(0.0,) * self._waveform_size,
            )
        mono = np.mean(samples, axis=1) if samples.ndim > 1 else samples
        rms = float(np.sqrt(np.mean(np.square(mono, dtype=np.float64))))
        if rms < self._silence_threshold:
            return AudioFrame(
                volume=0.0,
                spectrum=(0.0,) * self._bin_count,
                waveform=(0.0,) * self._waveform_size,
            )
        windowed = mono * np.hanning(mono.size)
        magnitudes = np.abs(np.fft.rfft(windowed))[1:]
        bass_energy = self._bass_energy(magnitudes, mono.size)
        if magnitudes.size < self._bin_count:
            magnitudes = np.pad(magnitudes, (0, self._bin_count - magnitudes.size))
        bands = np.array_split(magnitudes, self._bin_count)
        levels = tuple(float(np.clip(np.sqrt(np.mean(band)) * 3.0, 0.0, 1.0)) for band in bands)
        waveform = self._resample_waveform(mono)
        return AudioFrame(
            volume=float(np.clip(rms, 0.0, 1.0)),
            bass_energy=bass_energy,
            spectrum=levels,
            waveform=waveform,
        )

    def _bass_energy(self, magnitudes: NDArray[np.floating], sample_count: int) -> float:
        """Measure only the 20–100 Hz range, relative to the frame peak."""
        frequencies = np.fft.rfftfreq(sample_count, d=1.0 / self._sample_rate)[1:]
        band = magnitudes[(frequencies >= 20.0) & (frequencies <= 100.0)]
        if not band.size or not magnitudes.size:
            return 0.0
        window_compensated_peak = np.max(band) / max(sample_count * 0.25, 1e-8)
        return float(np.clip(window_compensated_peak, 0.0, 1.0))

    def _resample_waveform(self, samples: NDArray[np.floating]) -> tuple[float, ...]:
        positions = np.linspace(0, samples.size - 1, self._waveform_size)
        waveform = np.interp(positions, np.arange(samples.size), samples)
        peak = max(float(np.max(np.abs(waveform))), 1e-8)
        return tuple(float(value / peak) for value in waveform)
