"""Tests for portable thick-stroke geometry."""

import numpy as np

from musicscope.renderer.oscilloscope import OscilloscopeRenderer


def test_stroke_geometry_expands_a_line_segment_to_two_triangles() -> None:
    line = np.asarray(((0.0, 0.0), (1.0, 0.0)), dtype="f4")
    stroke = OscilloscopeRenderer._stroke_vertices(line, thickness=0.1)
    assert stroke.shape == (6, 2)
    assert {round(float(point[1]), 3) for point in stroke} == {-0.1, 0.1}


def test_idle_waveform_is_centered_on_the_scope_screen() -> None:
    renderer = object.__new__(OscilloscopeRenderer)
    renderer._sample_count = 8
    vertices = renderer._waveform_vertices(())
    assert set(vertices[:, 1]) == {0.0}


def test_waveform_interpolation_moves_toward_new_audio_over_multiple_frames() -> None:
    renderer = object.__new__(OscilloscopeRenderer)
    renderer._sample_count = 4
    renderer._display_waveform = None
    renderer._last_frame_time = None
    renderer._interpolate_waveform((0.0, 0.0, 0.0, 0.0), elapsed=0.0)
    frame = renderer._interpolate_waveform((1.0, 1.0, 1.0, 1.0), elapsed=0.016)
    assert 0.0 < frame[0] < 1.0

