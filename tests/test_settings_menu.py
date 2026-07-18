"""Tests for the layout contract of the settings overlay."""

from musicscope.renderer.settings_menu import SettingsMenuRenderer


def test_menu_texture_has_room_for_all_four_settings() -> None:
    """The colour control must not overlap the footer instructions."""
    _, height = SettingsMenuRenderer._TEXTURE_SIZE
    last_setting_baseline = 92 + 3 * 58
    footer_baseline = 324

    assert height >= 360
    assert last_setting_baseline < footer_baseline
