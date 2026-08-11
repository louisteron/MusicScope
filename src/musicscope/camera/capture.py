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
        self._source_lock = Lock()
        self._replacement: CameraFrameSource | None = None
        self._stopped = Event()
        self._thread: Thread | None = None

    @property
    def frame(self) -> np.ndarray | None:
        """Return the latest immutable camera frame, if one has arrived."""
        with self._lock:
            return self._frame

    def start(self) -> bool:
        """Begin capture once without blocking the render or audio threads."""
        if self._thread is not None:
            if self._thread.is_alive():
                return True
            self._thread = None
        self._stopped.clear()
        self._thread = Thread(target=self._run, name="camera-capture", daemon=True)
        self._thread.start()
        return True

    def replace_source(self, source: CameraFrameSource) -> None:
        """Switch cameras on the capture thread without interrupting audio rendering."""
        with self._source_lock:
            self._replacement = source

    def stop(self) -> None:
        """Stop capture and release the device."""
        self._stopped.set()
        with self._source_lock:
            self._source.close()
        if self._thread is not None:
            self._thread.join(timeout=0.20)
            if not self._thread.is_alive():
                self._thread = None
        with self._lock:
            self._frame = None

    def _run(self) -> None:
        source = self._source
        opened = False
        missed_frames = 0
        try:
            while not self._stopped.is_set():
                replacement = self._take_replacement()
                if replacement is not None:
                    if opened:
                        source.close()
                    source = replacement
                    opened = False
                    missed_frames = 0
                    with self._lock:
                        self._frame = None
                if not opened:
                    try:
                        opened = source.open()
                    except Exception as error:
                        self._logger.warning(
                            "Camera source could not open: %s", type(error).__name__
                        )
                        opened = False
                    if not opened:
                        self._stopped.wait(0.10)
                        continue
                try:
                    frame = source.read_frame()
                except Exception as error:
                    self._logger.warning("Camera source disconnected: %s", type(error).__name__)
                    source.close()
                    opened = False
                    self._stopped.wait(0.10)
                    continue
                if frame is not None:
                    missed_frames = 0
                    with self._lock:
                        self._frame = frame
                    continue
                missed_frames += 1
                if missed_frames == 60:
                    self._logger.warning("Camera is open but is not producing frames.")
                    source.close()
                    opened = False
                    missed_frames = 0
                self._stopped.wait(0.01)
        finally:
            source.close()

    def _take_replacement(self) -> CameraFrameSource | None:
        """Atomically move a pending source change onto the capture thread."""
        with self._source_lock:
            replacement = self._replacement
            self._replacement = None
            if replacement is not None:
                self._source = replacement
            return replacement
