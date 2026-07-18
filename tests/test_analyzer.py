"""Tests for deterministic audio analysis."""

import numpy as np

from musicscope.audio.analyzer import AudioAnalyzer


def test_analyzer_returns_zero_for_empty_samples() -> None:
    frame = AudioAnalyzer(bin_count=4).analyze(np.array([], dtype=np.float32))
    assert frame.volume == 0.0
    assert frame.spectrum == (0.0, 0.0, 0.0, 0.0)
    assert len(frame.waveform) == 512


def test_analyzer_calculates_rms_volume() -> None:
    samples = np.array([[-0.5], [0.5]], dtype=np.float32)
    assert AudioAnalyzer().analyze(samples).volume == 0.5


def test_analyzer_exposes_requested_number_of_frequency_bands() -> None:
    samples = np.sin(np.linspace(0, 20 * np.pi, 1_024, dtype=np.float32))
    assert len(AudioAnalyzer(bin_count=16).analyze(samples).spectrum) == 16


def test_analyzer_normalizes_waveform_to_a_phosphor_trace() -> None:
    samples = np.array([-0.25, 0.5, -0.5, 0.25], dtype=np.float32)
    waveform = AudioAnalyzer(waveform_size=8).analyze(samples).waveform
    assert len(waveform) == 8
    assert max(abs(value) for value in waveform) == 1.0


def test_analyzer_gates_near_silent_input() -> None:
    frame = AudioAnalyzer(waveform_size=8).analyze(np.full(32, 0.001, dtype=np.float32))
    assert frame.volume == 0.0
    assert frame.waveform == (0.0,) * 8


def test_analyzer_isolates_the_20_to_100_hz_bass_band() -> None:
    sample_rate = 4_096
    samples = np.arange(sample_rate, dtype=np.float32) / sample_rate
    analyzer = AudioAnalyzer(sample_rate=sample_rate)

    low_bass = analyzer.analyze(np.sin(2 * np.pi * 60 * samples)).bass_energy
    midrange = analyzer.analyze(np.sin(2 * np.pi * 300 * samples)).bass_energy

    assert low_bass > 0.9
    assert midrange < 0.01


def test_analyzer_scales_bass_energy_with_the_input_level() -> None:
    sample_rate = 4_096
    samples = np.arange(sample_rate, dtype=np.float32) / sample_rate
    analyzer = AudioAnalyzer(sample_rate=sample_rate)

    loud = analyzer.analyze(np.sin(2 * np.pi * 60 * samples)).bass_energy
    quiet = analyzer.analyze(0.05 * np.sin(2 * np.pi * 60 * samples)).bass_energy

    assert 0.04 < quiet < 0.06
    assert loud > quiet * 10
