"""Tests for physical CD playback process ownership."""

from musicscope.audio.cd_player import CdPlayer


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


def test_cd_player_launches_mpv_for_the_selected_drive() -> None:
    commands: list[list[str]] = []

    def start(command: list[str], **_kwargs: object) -> FakeProcess:
        commands.append(command)
        return FakeProcess()

    player = CdPlayer(device="/dev/sr0", start_process=start, mounted_tracks=lambda: ())

    player.start()

    assert commands == [["mpv", "--no-video", "--keep-open=no", "--cdda-device=/dev/sr0", "cdda://"]]


def test_cd_player_stops_its_owned_process() -> None:
    process = FakeProcess()
    player = CdPlayer(start_process=lambda *_args, **_kwargs: process)
    player.start()

    player.stop()

    assert process.terminated


def test_cd_player_routes_playback_to_the_visualizer_loopback() -> None:
    commands: list[list[str]] = []

    def start(command: list[str], **_kwargs: object) -> FakeProcess:
        commands.append(command)
        return FakeProcess()

    def resolve(name: str) -> str | None:
        return "coreaudio/blackhole" if name == "BlackHole 2ch" else None

    player = CdPlayer(
        audio_device="BlackHole 2ch",
        start_process=start,
        audio_device_resolver=resolve,
    )

    player.start()

    assert "--audio-device=coreaudio/blackhole" in commands[0]
