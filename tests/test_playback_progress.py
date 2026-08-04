"""Tests for mapping pointer coordinates onto the CD transport rail."""

import pytest

from musicscope.renderer.playback_progress import PlaybackProgressRenderer


def test_progress_cursor_mapping_uses_the_visible_centered_rail() -> None:
    """The two ends of the drawn rail map to the start and end of a track."""
    aspect = 16 / 9
    left = (1.0 - 1.30 / aspect) * 0.5
    right = (1.0 + 1.30 / aspect) * 0.5

    assert PlaybackProgressRenderer.fraction_from_cursor(
        left * 1600, 1600, aspect
    ) == pytest.approx(0.0)
    assert PlaybackProgressRenderer.fraction_from_cursor(
        right * 1600, 1600, aspect
    ) == pytest.approx(1.0)
