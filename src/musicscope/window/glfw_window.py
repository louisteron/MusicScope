"""A narrow GLFW wrapper with no rendering responsibilities."""

from collections import deque
from dataclasses import dataclass

import glfw


@dataclass(frozen=True, slots=True)
class KeyPress:
    """One GLFW key press including its modifier keys."""

    key: int
    modifiers: int


class GlfwWindow:
    """Create, update and destroy a single OpenGL-capable GLFW window."""

    def __init__(self, title: str, width: int, height: int, fullscreen: bool = False) -> None:
        self._title = title
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._window: glfw._GLFWwindow | None = None
        self._pressed_keys: deque[KeyPress] = deque()
        self._mouse_presses: deque[tuple[float, float]] = deque()
        self._key_callback = self._on_key
        self._mouse_callback = self._on_mouse_button

    def open(self) -> None:
        """Initialize GLFW and create the native window."""
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed.")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        monitor = glfw.get_primary_monitor() if self._fullscreen else None
        self._window = glfw.create_window(self._width, self._height, self._title, monitor, None)
        if self._window is None:
            glfw.terminate()
            raise RuntimeError("GLFW could not create an OpenGL window.")
        glfw.make_context_current(self._window)
        glfw.swap_interval(1)
        glfw.set_key_callback(self._window, self._key_callback)
        glfw.set_mouse_button_callback(self._window, self._mouse_callback)

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

    @property
    def window_size(self) -> tuple[int, int]:
        """Return the logical window size used by GLFW cursor coordinates."""
        if self._window is None:
            raise RuntimeError("Window is not open.")
        return glfw.get_window_size(self._window)

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
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._mouse_presses.append(glfw.get_cursor_pos(window))
