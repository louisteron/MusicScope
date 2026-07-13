"""A narrow GLFW wrapper with no rendering responsibilities."""

from collections import deque

import glfw


class GlfwWindow:
    """Create, update and destroy a single OpenGL-capable GLFW window."""

    def __init__(self, title: str, width: int, height: int, fullscreen: bool = False) -> None:
        self._title = title
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._window: glfw._GLFWwindow | None = None
        self._pressed_keys: deque[int] = deque()

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
        glfw.set_key_callback(self._window, self._on_key)

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

    def consume_pressed_keys(self) -> tuple[int, ...]:
        """Return and clear keyboard presses accumulated since the last frame."""
        keys = tuple(self._pressed_keys)
        self._pressed_keys.clear()
        return keys

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
        _modifiers: int,
    ) -> None:
        if action == glfw.PRESS:
            self._pressed_keys.append(key)
