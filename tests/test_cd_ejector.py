"""Tests for native CD ejection commands."""

import subprocess

from musicscope.audio.cd_ejector import CdEjector


def test_ejector_uses_drutil_on_macos() -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    assert CdEjector(platform="darwin", run=run).eject()
    assert commands == [["drutil", "tray", "eject"]]


def test_ejector_uses_device_on_linux() -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    assert CdEjector(device="/dev/sr0", platform="linux", run=run).eject()
    assert commands == [["eject", "/dev/sr0"]]
