"""Tests for playlist side-panel interaction mapping."""

from musicscope.core.playlist_menu import PlaylistAction, PlaylistMenu


def test_playlist_menu_maps_track_and_delete_rows() -> None:
    menu = PlaylistMenu()
    menu.toggle()

    assert menu.action_at(700, 210, 1000, 1000, 3) == (PlaylistAction.TRACK, 1)
    assert menu.action_at(900, 210, 1000, 1000, 3) == (PlaylistAction.DELETE, 1)


def test_playlist_menu_maps_clear_and_limits_rows() -> None:
    menu = PlaylistMenu()
    menu.toggle()

    assert menu.action_at(700, 870, 1000, 1000, 1) == (PlaylistAction.CLEAR, None)
    assert menu.track_index_at(700, 820, 1000, 1000, 20) is None


def test_playlist_menu_scrolls_and_offsets_clicked_rows() -> None:
    menu = PlaylistMenu()
    menu.toggle()

    menu.scroll(3, 15)

    assert menu.offset == 3
    assert menu.track_index_at(700, 210, 1000, 1000, 15) == 4
