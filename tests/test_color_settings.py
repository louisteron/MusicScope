"""Tests for shared runtime colour modes."""

from musicscope.renderer.color_settings import ColorMode, ColorSettings, PhosphorColor


def test_theme_mode_uses_the_cover_dominant_color() -> None:
    colors = ColorSettings(mode=ColorMode.NEON_GREEN, primary_color=(1.0, 0.25, 0.5))

    colors.cycle_mode(2)

    assert colors.mode is ColorMode.COVER_THEME
    assert colors.theme_color == (1.0, 0.25, 0.5)


def test_cover_neon_keeps_the_global_elements_green() -> None:
    colors = ColorSettings(mode=ColorMode.NEON_GREEN, primary_color=(1.0, 0.25, 0.5))

    colors.cycle_mode(1)

    assert colors.mode is ColorMode.COVER_NEON
    assert colors.theme_color == (0.10, 1.0, 0.34)


def test_cover_neon_is_the_default_mode() -> None:
    assert ColorSettings().mode is ColorMode.COVER_NEON


def test_environment_palette_changes_the_global_phosphor_color() -> None:
    colors = ColorSettings(phosphor_color=PhosphorColor.GREEN)

    colors.cycle_phosphor_color(1)

    assert colors.phosphor_color is PhosphorColor.WHITE
    assert colors.theme_color == (0.92, 1.0, 0.96)
