"""Tests for runtime oscilloscope settings controls."""

from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.renderer.color_settings import ColorMode, ColorSettings
from musicscope.renderer.oscillation_settings import OscillationSettings


def test_menu_toggles_and_formats_the_selected_setting() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.toggle()

    assert menu.visible
    assert menu.lines()[0].startswith("> AMPLITUDE")


def test_menu_adjusts_the_selected_setting() -> None:
    settings = OscillationSettings()
    menu = OscillationMenu(settings, ColorSettings())

    menu.adjust_selected(1)

    assert settings.amplitude == 0.52


def test_menu_selection_wraps() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.move_selection(-1)

    assert menu.lines()[-1].startswith("> COLOR")


def test_menu_cycles_the_color_mode() -> None:
    colors = ColorSettings()
    menu = OscillationMenu(OscillationSettings(), colors)
    menu.move_selection(-1)

    menu.adjust_selected(1)

    assert colors.mode is ColorMode.COVER_NEON
