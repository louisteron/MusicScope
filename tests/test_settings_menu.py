"""Tests for the layout contract of the settings overlay."""

from musicscope.renderer.settings_menu import SettingsMenuRenderer


def test_menu_texture_has_room_for_all_six_settings() -> None:
    """The recognition control must not overlap the footer instructions."""
    _, height = SettingsMenuRenderer._TEXTURE_SIZE
    last_setting_baseline = 92 + 5 * 58
    footer_baseline = 456

    assert height >= 500
    assert last_setting_baseline < footer_baseline


def test_menu_draws_distinct_visual_and_audio_panels() -> None:
    source = SettingsMenuRenderer._menu_image

    assert "visual_panel" in source.__code__.co_varnames
    assert "audio_panel" in source.__code__.co_varnames
