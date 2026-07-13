"""Tests for deterministic audio analysis."""

import numpy as np

from musicscope.audio.analyzer import AudioAnalyzer


def test_analyzer_returns_zero_for_empty_samples() -> None:
    frame = AudioAnalyzer(bin_count=4).analyze(np.array([], dtype=np.float32))
    assert frame.volume == 0.0
    assert frame.spectrum == (0.0, 0.0, 0.0, 0.0)


def test_analyzer_calculates_rms_volume() -> None:
    samples = np.array([[-0.5], [0.5]], dtype=np.float32)
    assert AudioAnalyzer().analyze(samples).volume == 0.5


def test_analyzer_exposes_requested_number_of_frequency_bands() -> None:
    samples = np.sin(np.linspace(0, 20 * np.pi, 1_024, dtype=np.float32))
    assert len(AudioAnalyzer(bin_count=16).analyze(samples).spectrum) == 16
