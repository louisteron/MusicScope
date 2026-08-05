"""mpv-backed playback for a local MusicScope playlist."""

import logging
import subprocess
from collections.abc import Callable
from pathlib import Path

from musicscope.audio.cd_player import AudioDeviceResolver, Process, ProcessStarter
from musicscope.audio.mpv_track_monitor import MpvTrackMonitor


class LocalPlaylistPlayer:
    """Play local audio files sequentially without owning playlist metadata."""

    def __init__(
        self,
        audio_device: str | None = None,
        executable: str = "mpv",
        start_process: ProcessStarter = subprocess.Popen,
        audio_device_resolver: AudioDeviceResolver | None = None,
        on_track_change: Callable[[int], None] | None = None,
        on_playback_time: Callable[[float], None] | None = None,
        on_duration: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._audio_device = audio_device
        self._executable = executable
        self._start_process = start_process
        self._audio_device_resolver = audio_device_resolver
        self._on_track_change = on_track_change
        self._on_playback_time = on_playback_time
        self._on_duration = on_duration
        self._logger = logger or logging.getLogger("musicscope")
        self._process: Process | None = None
        self._track_monitor: MpvTrackMonitor | None = None

    def play(self, paths: tuple[Path, ...], start_at: int = 1) -> None:
        """Replace the current playlist and begin sequential playback."""
        if not paths:
            return
        self.stop()
        command = [self._executable, "--no-video", "--keep-open=no"]
        if start_at > 1:
            command.append(f"--playlist-start={min(start_at, len(paths)) - 1}")
        self._add_audio_device(command)
        if any((self._on_track_change, self._on_playback_time, self._on_duration)):
            self._track_monitor = MpvTrackMonitor(
                self._on_track_change or self._ignore_track_change,
                self._on_playback_time,
                self._on_duration,
            )
            if self._track_monitor.available:
                command.append(self._track_monitor.input_argument)
        command.extend(str(path) for path in paths)
        try:
            self._process = self._start_process(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self._logger.warning("Local playlist playback unavailable: install mpv.")
            return
        if self._track_monitor is not None:
            self._track_monitor.start()
        self._logger.info("Starting local playlist with %s track(s).", len(paths))

    def stop(self) -> None:
        """Stop only the mpv process owned by this playlist player."""
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

    def _add_audio_device(self, command: list[str]) -> None:
        if self._audio_device is None or self._audio_device_resolver is None:
            return
        device = self._audio_device_resolver(self._audio_device)
        if device is not None:
            command.append(f"--audio-device={device}")

    @staticmethod
    def _ignore_track_change(_number: int) -> None:
        """Provide mpv monitoring when only timing callbacks are requested."""
