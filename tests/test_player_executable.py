"""Tests for locating the optional packaged mpv runtime."""

from pathlib import Path

from musicscope.audio.player_executable import resolve_mpv_executable


def test_resolver_uses_packaged_mpv_for_a_frozen_windows_build(tmp_path: Path) -> None:
    executable = tmp_path / "MusicScope.exe"
    bundled = tmp_path / "mpv" / "mpv.exe"
    bundled.parent.mkdir()
    bundled.touch()

    assert resolve_mpv_executable(
        platform="win32", frozen=True, executable=executable
    ) == str(bundled)


def test_resolver_uses_path_mpv_when_no_windows_runtime_is_packaged(tmp_path: Path) -> None:
    assert resolve_mpv_executable(
        platform="linux", frozen=True, executable=tmp_path / "MusicScope"
    ) == "mpv"
