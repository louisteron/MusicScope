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


def test_environment_palette_exposes_neon_red_pink_and_yellow() -> None:
    assert ColorSettings(phosphor_color=PhosphorColor.RED).theme_color == (1.0, 0.08, 0.12)
    assert ColorSettings(phosphor_color=PhosphorColor.PINK).theme_color == (1.0, 0.12, 0.62)
    assert ColorSettings(phosphor_color=PhosphorColor.YELLOW).theme_color == (1.0, 0.84, 0.08)
