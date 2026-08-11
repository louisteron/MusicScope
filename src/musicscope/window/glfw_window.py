"""A narrow GLFW wrapper with no rendering responsibilities."""

import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import glfw
from PIL import Image


@dataclass(frozen=True, slots=True)
class KeyPress:
    """One GLFW key press including its modifier keys."""

    key: int
    modifiers: int


@dataclass(frozen=True, slots=True)
class MouseButtonEvent:
    """One GLFW mouse-button transition in logical window coordinates."""

    x: float
    y: float
    action: int


class GlfwWindow:
    """Create, update and destroy a single OpenGL-capable GLFW window."""

    def __init__(self, title: str, width: int, height: int, fullscreen: bool = False) -> None:
        self._title = title
        self._width = width
        self._height = height
        self._start_fullscreen = fullscreen
        self._fullscreen = False
        self._window: glfw._GLFWwindow | None = None
        self._windowed_bounds: tuple[int, int, int, int] | None = None
        self._pressed_keys: deque[KeyPress] = deque()
        self._mouse_presses: deque[tuple[float, float]] = deque()
        self._mouse_button_events: deque[MouseButtonEvent] = deque()
        self._dropped_files: deque[Path] = deque()
        self._key_callback = self._on_key
        self._mouse_callback = self._on_mouse_button
        self._drop_callback = self._on_drop
        self._maximize_callback = self._on_maximize

    def open(self) -> None:
        """Initialize GLFW and create the native window."""
        self._set_windows_app_id()
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed.")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)
        self._window = glfw.create_window(self._width, self._height, self._title, None, None)
        if self._window is None:
            glfw.terminate()
            raise RuntimeError("GLFW could not create an OpenGL window.")
        self._set_taskbar_icon()
        glfw.make_context_current(self._window)
        glfw.swap_interval(1)
        glfw.set_key_callback(self._window, self._key_callback)
        glfw.set_mouse_button_callback(self._window, self._mouse_callback)
        glfw.set_drop_callback(self._window, self._drop_callback)
        glfw.set_window_maximize_callback(self._window, self._maximize_callback)
        x, y = glfw.get_window_pos(self._window)
        width, height = glfw.get_window_size(self._window)
        self._windowed_bounds = (x, y, width, height)
        if self._start_fullscreen:
            self.enter_fullscreen()

    @property
    def is_fullscreen(self) -> bool:
        """Whether the window currently occupies its monitor without decorations."""
        return self._fullscreen

    def enter_fullscreen(self) -> None:
        """Move the window onto the primary monitor as a true fullscreen window."""
        if self._window is None or self._fullscreen:
            return
        monitor = glfw.get_primary_monitor()
        if monitor is None:
            return
        mode = glfw.get_video_mode(monitor)
        if mode is None:
            return
        if self._windowed_bounds is None:
            x, y = glfw.get_window_pos(self._window)
            width, height = glfw.get_window_size(self._window)
            self._windowed_bounds = (x, y, width, height)
        width, height = mode.size
        glfw.set_window_monitor(self._window, monitor, 0, 0, width, height, mode.refresh_rate)
        self._fullscreen = True

    def exit_fullscreen(self) -> None:
        """Restore the last windowed size after the user presses Escape."""
        if self._window is None or not self._fullscreen:
            return
        x, y, width, height = self._windowed_bounds or (80, 80, self._width, self._height)
        glfw.set_window_monitor(self._window, None, x, y, width, height, glfw.DONT_CARE)
        self._fullscreen = False

    @property
    def should_close(self) -> bool:
        """Whether the window manager has requested shutdown."""
        return self._window is None or glfw.window_should_close(self._window)

    @property
    def framebuffer_size(self) -> tuple[int, int]:
        """Return the physical pixel dimensions used by OpenGL."""
        if self._window is None:
            raise RuntimeError("Window is not open.")
        return glfw.get_framebuffer_size(self._window)

    def poll_events(self) -> None:
        """Process pending window-system events."""
        glfw.poll_events()

    def consume_pressed_keys(self) -> tuple[KeyPress, ...]:
        """Return and clear keyboard presses accumulated since the last frame."""
        keys = tuple(self._pressed_keys)
        self._pressed_keys.clear()
        return keys

    def consume_mouse_presses(self) -> tuple[tuple[float, float], ...]:
        """Return mouse press positions in window coordinates."""
        presses = tuple(self._mouse_presses)
        self._mouse_presses.clear()
        return presses

    def consume_mouse_button_events(self) -> tuple[MouseButtonEvent, ...]:
        """Return left-button press/release events for drag-based controls."""
        events = tuple(self._mouse_button_events)
        self._mouse_button_events.clear()
        self._mouse_presses.clear()
        return events

    def consume_dropped_files(self) -> tuple[Path, ...]:
        """Return files and folders dropped onto the window."""
        paths = tuple(self._dropped_files)
        self._dropped_files.clear()
        return paths

    @property
    def window_size(self) -> tuple[int, int]:
        """Return the logical window size used by GLFW cursor coordinates."""
        if self._window is None:
            raise RuntimeError("Window is not open.")
        return glfw.get_window_size(self._window)

    @property
    def cursor_position(self) -> tuple[float, float]:
        """Return the current logical cursor coordinates."""
        if self._window is None:
            raise RuntimeError("Window is not open.")
        return glfw.get_cursor_pos(self._window)

    def present(self) -> None:
        """Swap front and back buffers."""
        if self._window is None:
            raise RuntimeError("Window is not open.")
        glfw.swap_buffers(self._window)

    def close(self) -> None:
        """Release native resources. This method is idempotent."""
        if self._window is not None:
            glfw.destroy_window(self._window)
            self._window = None
        glfw.terminate()

    def _set_taskbar_icon(self) -> None:
        """Apply the bundled icon to the active native Windows window."""
        if sys.platform != "win32" or self._window is None:
            return
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "musicscope-logo.png"
        try:
            with Image.open(icon_path) as source:
                icon = source.copy()
            glfw.set_window_icon(self._window, 1, [icon])
        except OSError:
            # The executable icon remains available even if an asset is missing.
            return

    @staticmethod
    def _set_windows_app_id() -> None:
        """Give Windows a stable taskbar identity for the MusicScope executable."""
        if sys.platform != "win32":
            return
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("io.musicscope.app")
        except (AttributeError, OSError):
            return

    def _on_maximize(self, _window: glfw._GLFWwindow, maximized: bool) -> None:
        """Turn the Windows maximize button into a borderless fullscreen action."""
        if sys.platform == "win32" and maximized:
            self.enter_fullscreen()

    def _on_key(
        self,
        _window: glfw._GLFWwindow,
        key: int,
        _scancode: int,
        action: int,
        modifiers: int,
    ) -> None:
        if action == glfw.PRESS:
            self._pressed_keys.append(KeyPress(key, modifiers))

    def _on_mouse_button(
        self,
        window: glfw._GLFWwindow,
        button: int,
        action: int,
        _modifiers: int,
    ) -> None:
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        cursor_x, cursor_y = glfw.get_cursor_pos(window)
        self._mouse_button_events.append(MouseButtonEvent(cursor_x, cursor_y, action))
        if action == glfw.PRESS:
            self._mouse_presses.append((cursor_x, cursor_y))

    def _on_drop(self, _window: glfw._GLFWwindow, paths: list[str]) -> None:
        self._dropped_files.extend(Path(path) for path in paths)
