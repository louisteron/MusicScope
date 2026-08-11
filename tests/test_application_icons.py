"""Tests for the platform icons used by native MusicScope builds."""

from pathlib import Path

from PIL import Image

from musicscope.window import glfw_window


def test_packaging_icons_are_valid_multiresolution_images() -> None:
    packaging_directory = Path(__file__).parents[1] / "packaging"

    with Image.open(packaging_directory / "musicscope.ico") as windows_icon:
        assert windows_icon.format == "ICO"
        assert windows_icon.size == (256, 256)
    with Image.open(packaging_directory / "musicscope.icns") as mac_icon:
        assert mac_icon.format == "ICNS"
        assert mac_icon.size == (1024, 1024)


def test_windows_window_uses_the_bundled_taskbar_icon(monkeypatch) -> None:
    applied: list[tuple[object, int, list[Image.Image]]] = []
    monkeypatch.setattr(glfw_window.sys, "platform", "win32")
    monkeypatch.setattr(glfw_window.glfw, "set_window_icon", lambda *args: applied.append(args))
    window = glfw_window.GlfwWindow("MusicScope", 800, 600)
    window._window = object()  # noqa: SLF001 - native handle substitute for this adapter test.

    window._set_taskbar_icon()  # noqa: SLF001 - verify the native-window integration.

    assert len(applied) == 1
    assert applied[0][1] == 1
    assert applied[0][2][0].size == (2048, 2048)
