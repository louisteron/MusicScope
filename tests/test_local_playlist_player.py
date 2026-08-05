"""Tests for the local mpv playlist player."""

from pathlib import Path

from musicscope.audio.local_playlist_player import LocalPlaylistPlayer


class FakeProcess:
    def __init__(self) -> None:
        self.running = True
        self.terminated = False

    def poll(self) -> int | None:
        return None if self.running else 0

    def terminate(self) -> None:
        self.terminated = True
        self.running = False

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def kill(self) -> None:
        self.running = False


def test_local_playlist_player_launches_tracks_in_order() -> None:
    commands: list[list[str]] = []
    first = Path("/music/first.mp3")
    second = Path("/music/second.flac")

    def start(command: list[str], **_kwargs: object) -> FakeProcess:
        commands.append(command)
        return FakeProcess()

    player = LocalPlaylistPlayer(start_process=start)
    player.play((first, second))

    assert commands == [["mpv", "--no-video", "--keep-open=no", str(first), str(second)]]


def test_local_playlist_player_routes_to_visualizer_loopback() -> None:
    commands: list[list[str]] = []

    def start(command: list[str], **_kwargs: object) -> FakeProcess:
        commands.append(command)
        return FakeProcess()

    player = LocalPlaylistPlayer(
        audio_device="BlackHole 2ch",
        audio_device_resolver=lambda _name: "coreaudio/blackhole",
        start_process=start,
    )
    player.play((Path("/music/song.mp3"),))

    assert "--audio-device=coreaudio/blackhole" in commands[0]


def test_local_playlist_player_enables_mpv_timing_for_lyrics(monkeypatch) -> None:
    class FakeMonitor:
        available = True
        input_argument = "--input-ipc-server=/tmp/test-mpv.sock"

        def __init__(self, on_track_change, on_playback_time, on_duration) -> None:
            self.on_track_change = on_track_change
            self.on_playback_time = on_playback_time
            self.on_duration = on_duration
            monitors.append(self)

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    monitors: list[FakeMonitor] = []
    monkeypatch.setattr("musicscope.audio.local_playlist_player.MpvTrackMonitor", FakeMonitor)
    player = LocalPlaylistPlayer(
        start_process=lambda *_args, **_kwargs: FakeProcess(),
        on_playback_time=lambda _seconds: None,
    )

    player.play((Path("/music/song.mp3"),))

    assert len(monitors) == 1
    assert monitors[0].on_playback_time is not None
