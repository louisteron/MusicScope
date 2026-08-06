"""Tests for the neon outline artwork shader contract."""

from musicscope.renderer.artwork import ArtworkRenderer


def test_artwork_shader_uses_contrast_and_alpha_edges() -> None:
    shader = ArtworkRenderer._FRAGMENT_SHADER

    assert "u_texel_size" in shader
    assert "contrast_edge" in shader
    assert "alpha_edge" in shader
    assert "if (trace < 0.02 && logo_fill < 0.01) discard" in shader
    assert "bass_warp" in shader
    assert "shockwave" in shader
    assert "u_color_mode" in shader
    assert "u_theme_color" in shader
    assert "u_logo" in shader
    assert "logo_fill" in shader


def test_artwork_shader_compensates_for_window_aspect_ratio() -> None:
    shader = ArtworkRenderer._VERTEX_SHADER

    assert "uniform float u_aspect_ratio" in shader
    assert "in_position.x / u_aspect_ratio" in shader


def test_cover_bass_motion_responds_to_pronounced_bass() -> None:
    bass_energy = 0.9

    assert ArtworkRenderer._bass_motion(bass_energy) > 0.9


def test_cover_bass_motion_ignores_low_bass_energy() -> None:
    bass_energy = 0.05

    assert ArtworkRenderer._bass_motion(bass_energy) == 0.0
