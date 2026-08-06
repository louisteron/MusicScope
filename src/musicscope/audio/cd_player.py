"""Physical audio-CD playback through the external mpv player."""

import logging
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from musicscope.audio.mpv_track_monitor import MpvTrackMonitor
from musicscope.audio.player_executable import resolve_mpv_executable


class Process(Protocol):
    """The small process surface owned by the CD player."""

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def kill(self) -> None: ...


ProcessStarter = Callable[..., Process]
MountedTracks = Callable[[], tuple[Path, ...]]
AudioDeviceResolver = Callable[[str], str | None]


class CdPlayer:
    """Launch and stop audio-CD playback without owning metadata lookup."""

    def __init__(
        self,
        device: str | None = None,
        audio_device: str | None = None,
        executable: str | None = None,
        start_process: ProcessStarter = subprocess.Popen,
        mounted_tracks: MountedTracks | None = None,
        audio_device_resolver: AudioDeviceResolver | None = None,
        on_track_change: Callable[[int], None] | None = None,
        on_playback_time: Callable[[float], None] | None = None,
        on_duration: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._device = device
        self._audio_device = audio_device
        self._executable = executable or resolve_mpv_executable()
        self._start_process = start_process
        self._mounted_tracks = mounted_tracks or self._macos_mounted_tracks
        self._audio_device_resolver = audio_device_resolver or self._resolve_mpv_audio_device
        self._on_track_change = on_track_change
        self._on_playback_time = on_playback_time
        self._on_duration = on_duration
        self._logger = logger or logging.getLogger("musicscope")
        self._process: Process | None = None
        self._track_monitor: MpvTrackMonitor | None = None

    def start(self) -> None:
        """Start playback of the inserted CD when mpv is available."""
        if self._process is not None and self._process.poll() is None:
            return
        command = [self._executable, "--no-video", "--keep-open=no"]
        self._add_audio_device(command)
        if self._on_track_change is not None:
            self._track_monitor = MpvTrackMonitor(
                self._on_track_change,
                self._on_playback_time,
                self._on_duration,
            )
            if self._track_monitor.available:
                command.append(self._track_monitor.input_argument)
        mounted_tracks = self._mounted_tracks() if sys.platform == "darwin" else ()
        if mounted_tracks:
            command.extend(str(track) for track in mounted_tracks)
        elif self._device is not None:
            command.append(f"--cdda-device={self._device}")
            command.append("cdda://")
        else:
            command.append("cdda://")
        try:
            self._process = self._start_process(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self._logger.warning("CD playback unavailable: install mpv to play audio CDs.")
            return
        if self._track_monitor is not None:
            self._track_monitor.start()
        self._logger.info("Starting audio CD playback through mpv.")

    def seek_to_fraction(self, fraction: float) -> bool:
        """Seek the current CD track when mpv's IPC controller is available."""
        if self._track_monitor is None:
            return False
        return self._track_monitor.seek_to_fraction(fraction)

    def _add_audio_device(self, command: list[str]) -> None:
        """Route CD playback into the selected loopback so it can be visualized."""
        if self._audio_device is None:
            return
        mpv_device = self._audio_device_resolver(self._audio_device)
        if mpv_device is None:
            self._logger.warning(
                "CD playback could not route to %s; using mpv's default output.",
                self._audio_device,
            )
            return
        command.append(f"--audio-device={mpv_device}")
        self._logger.info("Routing CD playback to visualizer input: %s", self._audio_device)

    def _resolve_mpv_audio_device(self, device_name: str) -> str | None:
        """Map a human-readable audio device name to mpv's backend-specific ID."""
        try:
            result = subprocess.run(
                [self._executable, "--audio-device=help", "--no-video"],
                capture_output=True,
                check=False,
                text=True,
                timeout=3.0,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        matches: list[str] = []
        for line in result.stdout.splitlines():
            if "' (" not in line:
                continue
            identifier, label = line.strip().split("' (", maxsplit=1)
            if device_name.casefold() in label.rstrip(")").casefold():
                matches.append(identifier.removeprefix("'"))
        return next((item for item in matches if item.startswith("coreaudio/")), None) or next(
            iter(matches), None
        )

    @staticmethod
    def _macos_mounted_tracks() -> tuple[Path, ...]:
        """Return tracks mounted by macOS's CDDA filesystem in playback order."""
        if not Path("/Volumes").is_dir():
            return ()
        tracks = [track for volume in Path("/Volumes").iterdir() for track in volume.glob("*.aiff")]
        return tuple(sorted(tracks, key=CdPlayer._track_number))

    @staticmethod
    def _track_number(track: Path) -> int:
        """Sort macOS CDDA files numerically instead of lexicographically."""
        prefix = track.name.split(" ", maxsplit=1)[0]
        return int(prefix) if prefix.isdigit() else 0

    def stop(self) -> None:
        """Stop only the player process owned by MusicScope."""
        if self._track_monitor is not None:
            self._track_monitor.stop()
            self._track_monitor = None
        if self._process is None or self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
