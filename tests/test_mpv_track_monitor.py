"""Tests for mpv playlist-position messages."""

from musicscope.audio.mpv_track_monitor import MpvTrackMonitor


def test_monitor_converts_mpv_playlist_positions_to_one_based_track_numbers() -> None:
    received: list[int] = []
    monitor = MpvTrackMonitor(received.append)

    monitor._handle_message('{"event":"property-change","name":"playlist-pos","data":2}')

    assert received == [3]


def test_monitor_ignores_unrelated_mpv_messages() -> None:
    received: list[int] = []
    monitor = MpvTrackMonitor(received.append)

    monitor._handle_message('{"event":"property-change","name":"pause","data":false}')

    assert received == []


def test_monitor_publishes_the_current_track_duration() -> None:
    received: list[float] = []
    monitor = MpvTrackMonitor(lambda _track: None, on_duration=received.append)

    monitor._handle_message('{"name":"duration","data":312.4}')

    assert received == [312.4]
