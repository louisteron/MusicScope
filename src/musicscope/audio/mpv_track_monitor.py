"""Monitor mpv's current playlist position through its local IPC socket."""

import json
import socket
import sys
import time
from collections.abc import Callable
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4


class MpvTrackMonitor:
    """Publish one-based playlist track numbers while mpv plays an audio CD."""

    def __init__(
        self,
        on_track_change: Callable[[int], None],
        on_playback_time: Callable[[float], None] | None = None,
        on_duration: Callable[[float], None] | None = None,
    ) -> None:
        self._on_track_change = on_track_change
        self._on_playback_time = on_playback_time
        self._on_duration = on_duration
        self._socket_path = Path(f"/tmp/musicscope-mpv-{uuid4().hex}.sock")
        self._stopped = Event()
        self._thread: Thread | None = None
        self._socket: socket.socket | None = None

    @property
    def available(self) -> bool:
        """Whether this host supports mpv's Unix-domain IPC socket."""
        return sys.platform != "win32" and hasattr(socket, "AF_UNIX")

    @property
    def input_argument(self) -> str:
        """Return the mpv option enabling the local IPC server."""
        return f"--input-ipc-server={self._socket_path}"

    def start(self) -> None:
        """Connect asynchronously after mpv has created its IPC socket."""
        if not self.available or self._thread is not None:
            return
        self._thread = Thread(target=self._run, name="mpv-track-monitor", daemon=True)
        self._thread.start()

    def seek_to_fraction(self, fraction: float) -> bool:
        """Ask mpv to seek within the current track through its IPC socket."""
        if not self.available:
            return False
        percentage = max(0.0, min(1.0, fraction)) * 100.0
        payload = json.dumps({"command": ["seek", percentage, "absolute-percent"]}) + "\n"
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(str(self._socket_path))
            client.sendall(payload.encode())
            client.close()
        except OSError:
            return False
        return True

    def stop(self) -> None:
        """Stop monitoring and clean up the private socket path."""
        self._stopped.set()
        if self._socket is not None:
            self._socket.close()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None
        self._socket_path.unlink(missing_ok=True)

    def _run(self) -> None:
        for _ in range(30):
            if self._stopped.is_set():
                return
            try:
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(str(self._socket_path))
            except (OSError, ValueError):
                time.sleep(0.1)
                continue
            self._socket = client
            try:
                client.sendall(b'{"command":["observe_property",1,"playlist-pos"]}\n')
                client.sendall(b'{"command":["observe_property",2,"time-pos"]}\n')
                client.sendall(b'{"command":["observe_property",3,"duration"]}\n')
                with client.makefile("r", encoding="utf-8") as stream:
                    for line in stream:
                        if self._stopped.is_set():
                            return
                        self._handle_message(line)
            except (OSError, ValueError):
                return
            finally:
                client.close()
            return

    def _handle_message(self, message: str) -> None:
        """Translate mpv's zero-based playlist position to a track number."""
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        position = payload.get("data")
        if payload.get("name") == "playlist-pos" and isinstance(position, int) and position >= 0:
            self._on_track_change(position + 1)
        if (
            payload.get("name") == "time-pos"
            and isinstance(position, (int, float))
            and self._on_playback_time is not None
        ):
            self._on_playback_time(float(position))
        if (
            payload.get("name") == "duration"
            and isinstance(position, (int, float))
            and self._on_duration is not None
        ):
            self._on_duration(float(position))
