"""Threaded camera acquisition isolated from the OpenGL render loop."""

import logging
from threading import Event, Lock, Thread

import numpy as np

from musicscope.camera.source import CameraFrameSource


class CameraCapture:
    """Own one camera source and expose its most recent frame without blocking."""

    def __init__(self, source: CameraFrameSource, logger: logging.Logger | None = None) -> None:
        self._source = source
        self._logger = logger or logging.getLogger("musicscope")
        self._frame: np.ndarray | None = None
        self._lock = Lock()
        self._stopped = Event()
        self._thread: Thread | None = None

    @property
    def frame(self) -> np.ndarray | None:
        """Return the latest immutable camera frame, if one has arrived."""
        with self._lock:
            return self._frame

    def start(self) -> bool:
        """Begin capture once; return false when no camera is usable."""
        if self._thread is not None:
            return True
        if not self._source.open():
            return False
        self._stopped.clear()
        self._thread = Thread(target=self._run, name="camera-capture", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop capture and release the device."""
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._source.close()
        with self._lock:
            self._frame = None

    def _run(self) -> None:
        while not self._stopped.is_set():
            frame = self._source.read_frame()
            if frame is not None:
                with self._lock:
                    self._frame = frame
