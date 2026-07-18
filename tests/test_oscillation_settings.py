"""Tests for bounded waveform settings."""

from musicscope.renderer.oscillation_settings import OscillationSettings


def test_settings_clamp_amplitude_adjustments() -> None:
    settings = OscillationSettings(amplitude=0.84)

    settings.adjust("Amplitude", 1)

    assert settings.amplitude == 0.85
