"""Tests for AudD clip selection."""

import numpy as np

from musicscope.recognition.service import RecognitionService


def test_service_skips_silent_audio() -> None:
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=44_100,
        on_identification=lambda _result: None,
    )

    assert not service._has_audible_signal(np.zeros(44_100, dtype=np.float32))


def test_service_accepts_audible_audio() -> None:
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=44_100,
        on_identification=lambda _result: None,
    )

    assert service._has_audible_signal(np.full(44_100, 0.02, dtype=np.float32))
