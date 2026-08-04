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


def test_service_accepts_quiet_loopback_audio_and_normalises_the_clip() -> None:
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=44_100,
        on_identification=lambda _result: None,
    )
    quiet_audio = np.full(44_100, 0.0002, dtype=np.float32)

    normalised = service._normalise_clip(quiet_audio)

    assert service._has_audible_signal(quiet_audio)
    assert np.isclose(np.sqrt(np.mean(np.square(normalised))), 0.12)


def test_service_collects_audible_audio_without_needing_a_silence_reset() -> None:
    now = [0.0]
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=10,
        on_identification=lambda _result: None,
        request_cooldown_seconds=10,
        clock=lambda: now[0],
    )
    audible = np.full(10, 0.02, dtype=np.float32)

    assert service._should_collect(audible)
    service._next_request_at = 10.0
    assert not service._should_collect(audible)
    now[0] = 10.0

    assert service._should_collect(audible)


def test_service_never_collects_silence_after_the_cooldown() -> None:
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=10,
        on_identification=lambda _result: None,
        request_cooldown_seconds=10,
    )
    silence = np.zeros(10, dtype=np.float32)

    assert not service._should_collect(silence)


def test_service_keeps_collecting_a_clip_after_an_audible_start() -> None:
    service = RecognitionService(
        workflow=object(),  # type: ignore[arg-type]
        sample_rate=10,
        on_identification=lambda _result: None,
    )
    chunks: list[np.ndarray] = []
    audible = np.full(10, 0.02, dtype=np.float32)
    quiet = np.zeros(10, dtype=np.float32)

    if not chunks and service._should_collect(audible):
        chunks.append(audible)
    if chunks:
        chunks.append(quiet)

    assert len(chunks) == 2
