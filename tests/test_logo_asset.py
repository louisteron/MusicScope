"""Tests for the bundled reactive frog logo."""

from pathlib import Path

import pytest
from PIL import Image

from musicscope.renderer.artwork import ArtworkRenderer


def test_frog_logo_is_packaged_and_its_background_is_removed() -> None:
    path = Path(__file__).parents[1] / "src" / "musicscope" / "assets" / "frog.jpg"
    with Image.open(path) as image:
        prepared = ArtworkRenderer._prepare_image(image, isolate_foreground=True)
    assert prepared.size == (512, 512)
    assert prepared.getchannel("A").getextrema()[0] == 0


def test_jvb_logo_keeps_its_existing_transparency() -> None:
    """A transparent PNG must not go through the frog photograph mask."""
    path = Path(__file__).parents[1] / "src" / "musicscope" / "assets" / "logo-jvb.png"
    with Image.open(path) as image:
        prepared = ArtworkRenderer._prepare_image(image, isolate_foreground=False)

    assert prepared.getchannel("A").getextrema() == (0, 255)


def test_jvb_logo_can_be_fitted_without_its_transparent_padding() -> None:
    path = Path(__file__).parents[1] / "src" / "musicscope" / "assets" / "logo-jvb.png"
    with Image.open(path) as image:
        prepared = ArtworkRenderer._prepare_image(
            image,
            isolate_foreground=False,
            crop_transparent_border=True,
        )

    left, top, right, bottom = prepared.getchannel("A").getbbox()
    assert top == 0
    assert bottom == prepared.height
    assert right - left > prepared.width * 0.8


def test_ram_logo_has_a_transparent_background() -> None:
    path = Path(__file__).parents[1] / "src" / "musicscope" / "assets" / "logo-ram.png"
    with Image.open(path) as image:
        assert image.convert("RGBA").getchannel("A").getextrema()[0] == 0


@pytest.mark.parametrize("asset_name", ("disc-cd.png", "disc-vinyl.png"))
def test_disc_visuals_have_transparent_corners(asset_name: str) -> None:
    path = Path(__file__).parents[1] / "src" / "musicscope" / "assets" / asset_name
    with Image.open(path) as image:
        alpha = image.convert("RGBA").getchannel("A")

    assert alpha.getpixel((0, 0)) == 0


def test_artwork_is_contained_without_stretching() -> None:
    image = Image.new("RGBA", (400, 100), "white")

    prepared = ArtworkRenderer._prepare_image(image, isolate_foreground=False)

    assert prepared.size == (512, 512)
    assert prepared.getchannel("A").getbbox() == (0, 192, 512, 320)
