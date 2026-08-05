"""Interaction state and hit testing for the local playlist side panel."""

from enum import StrEnum


class PlaylistAction(StrEnum):
    """Actions available from the playlist side panel."""

    TRACK = "track"
    DELETE = "delete"
    CLEAR = "clear"


class PlaylistMenu:
    """Keep playlist-panel layout independent from GLFW and rendering."""

    _LEFT = 0.59
    _RIGHT = 0.98
    _ROWS_TOP = 0.208
    _ROW_HEIGHT = 0.053
    _MAX_VISIBLE_TRACKS = 10
    _DELETE_LEFT = 0.88
    _CLEAR_TOP = 0.825
    _CLEAR_BOTTOM = 0.90

    def __init__(self) -> None:
        self._visible = False

    @property
    def visible(self) -> bool:
        """Whether the playlist panel should be visible."""
        return self._visible

    @property
    def max_visible_tracks(self) -> int:
        """Return how many playlist rows fit in the side panel."""
        return self._MAX_VISIBLE_TRACKS

    def toggle(self) -> None:
        """Show or hide the side panel."""
        self._visible = not self._visible

    def action_at(
        self,
        cursor_x: float,
        cursor_y: float,
        window_width: int,
        window_height: int,
        playlist_size: int,
    ) -> tuple[PlaylistAction, int | None] | None:
        """Map a logical GLFW cursor position to a playlist control."""
        if not self._visible or not window_width or not window_height:
            return None
        x = cursor_x / window_width
        y = cursor_y / window_height
        if not self._LEFT <= x <= self._RIGHT:
            return None
        if self._CLEAR_TOP <= y <= self._CLEAR_BOTTOM:
            return (PlaylistAction.CLEAR, None)
        index = self.track_index_at(cursor_x, cursor_y, window_width, window_height, playlist_size)
        if index is None:
            return None
        return (PlaylistAction.DELETE if x >= self._DELETE_LEFT else PlaylistAction.TRACK, index)

    def track_index_at(
        self,
        cursor_x: float,
        cursor_y: float,
        window_width: int,
        window_height: int,
        playlist_size: int,
    ) -> int | None:
        """Return the row under the cursor, using one-based playlist positions."""
        if not window_width or not window_height:
            return None
        x = cursor_x / window_width
        y = cursor_y / window_height
        if not self._LEFT <= x <= self._RIGHT or y < self._ROWS_TOP:
            return None
        index = int((y - self._ROWS_TOP) / self._ROW_HEIGHT) + 1
        maximum = min(playlist_size, self._MAX_VISIBLE_TRACKS)
        return index if 1 <= index <= maximum else None
