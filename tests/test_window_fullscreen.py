"""Tests for native fullscreen transitions."""

from types import SimpleNamespace

from musicscope.window import glfw_window


def test_fullscreen_restores_window_bounds(monkeypatch) -> None:
    calls: list[tuple[object, object, int, int, int, int, int]] = []
    window = glfw_window.GlfwWindow("MusicScope", 1280, 720)
    window._window = object()  # noqa: SLF001 - substitute the GLFW native handle.
    window._windowed_bounds = (40, 50, 1280, 720)  # noqa: SLF001
    monitor = object()
    monkeypatch.setattr(glfw_window.glfw, "get_primary_monitor", lambda: monitor)
    monkeypatch.setattr(
        glfw_window.glfw,
        "get_video_mode",
        lambda _monitor: SimpleNamespace(size=(1920, 1080), refresh_rate=60),
    )
    monkeypatch.setattr(glfw_window.glfw, "set_window_monitor", lambda *args: calls.append(args))

    window.enter_fullscreen()

    assert window.is_fullscreen
    assert calls[-1] == (window._window, monitor, 0, 0, 1920, 1080, 60)  # noqa: SLF001

    window.exit_fullscreen()

    assert not window.is_fullscreen
    assert calls[-1] == (window._window, None, 40, 50, 1280, 720, glfw_window.glfw.DONT_CARE)  # noqa: SLF001


def test_windows_maximize_enters_fullscreen(monkeypatch) -> None:
    window = glfw_window.GlfwWindow("MusicScope", 1280, 720)
    entered: list[bool] = []
    monkeypatch.setattr(glfw_window.sys, "platform", "win32")
    monkeypatch.setattr(window, "enter_fullscreen", lambda: entered.append(True))

    window._on_maximize(object(), True)  # noqa: SLF001 - native callback adapter.

    assert entered == [True]
