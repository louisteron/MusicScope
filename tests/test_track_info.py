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
