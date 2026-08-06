"""Tests for the Windows speaker-loopback adapter."""

import numpy as np

from musicscope.audio.analyzer import AudioAnalyzer
from musicscope.audio.windows_loopback import WindowsLoopbackInput


def test_loopback_publishes_analyzed_frames_and_raw_samples() -> None:
    frames = []
    samples = []
    loopback = WindowsLoopbackInput(
        AudioAnalyzer(sample_rate=48_000),
        frames.append,
        sample_rate=48_000,
        block_size=4,
        on_samples=samples.append,
    )

    loopback._publish(np.array([[0.3, 0.3], [-0.3, -0.3]], dtype=np.float64))

    assert len(frames) == 1
    assert frames[0].volume > 0.0
    assert samples[0].dtype == np.float32
