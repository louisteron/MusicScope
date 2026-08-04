"""Tests for renderer-neutral track metadata labels."""

from musicscope.renderer.track_info import TrackInfoRenderer
from musicscope.scene.model import VisualState


def test_track_label_uses_title_and_artist() -> None:
    label = TrackInfoRenderer._label_for(
        VisualState(track_title="One More Time", artist_name="Daft Punk")
    )

    assert label == "ONE MORE TIME\nDAFT PUNK"


def test_track_label_is_hidden_until_metadata_exists() -> None:
    assert TrackInfoRenderer._label_for(VisualState()) is None


def test_track_label_can_include_the_album_track_number() -> None:
    label = TrackInfoRenderer._label_for(
        VisualState(track_title="Instant Crush", artist_name="Daft Punk", track_number=5),
        show_track_number=True,
    )

    assert label == "05 · INSTANT CRUSH\nDAFT PUNK"
