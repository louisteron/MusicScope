"""Tests for the platform icons used by native MusicScope builds."""

from pathlib import Path

from PIL import Image


def test_packaging_icons_are_valid_multiresolution_images() -> None:
    packaging_directory = Path(__file__).parents[1] / "packaging"

    with Image.open(packaging_directory / "musicscope.ico") as windows_icon:
        assert windows_icon.format == "ICO"
        assert windows_icon.size == (256, 256)
    with Image.open(packaging_directory / "musicscope.icns") as mac_icon:
        assert mac_icon.format == "ICNS"
        assert mac_icon.size == (1024, 1024)
