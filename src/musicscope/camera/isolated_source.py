"""Crash-isolated macOS camera capture backed by a child process."""

import logging
import multiprocessing
import time
from io import BytesIO

import numpy as np
from PIL import Image


def _capture_worker(index: int, connection: object) -> None:
    """Read a camera in a disposable process so AVFoundation cannot kill the app."""
    import cv2

    capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        capture.release()
        connection.close()
        return
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    capture.set(cv2.CAP_PROP_FPS, 30)
    try:
        while True:
            success, frame = capture.read()
            if not success:
                time.sleep(0.02)
                continue
            encoded, payload = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if not encoded:
                continue
            connection.send_bytes(payload.tobytes())
    except (BrokenPipeError, EOFError):
        return
    finally:
        capture.release()
        connection.close()


class IsolatedCameraSource:
    """Receive JPEG camera frames from a child process on platforms with unstable drivers."""

    def __init__(self, index: int = 0, logger: logging.Logger | None = None) -> None:
        self._index = index
        self._logger = logger or logging.getLogger("musicscope")
        self._process: multiprocessing.Process | None = None
        self._connection: object | None = None

    def open(self) -> bool:
        """Start the isolated capture worker without opening AVFoundation in this process."""
        self.close()
        context = multiprocessing.get_context("spawn")
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=_capture_worker, args=(self._index, sender), daemon=True)
        process.start()
        sender.close()
        self._process = process
        self._connection = receiver
        self._logger.info("Camera background started in isolated mode (camera %s).", self._index)
        return True

    def read_frame(self) -> np.ndarray | None:
        """Return the most recent decoded RGB frame, or None if the worker stopped."""
        if self._connection is None or self._process is None:
            return None
        if not self._process.is_alive():
            self._logger.warning("Camera worker stopped; restarting capture safely.")
            self.close()
            return None
        latest: bytes | None = None
        try:
            while self._connection.poll():
                latest = self._connection.recv_bytes()
        except (EOFError, OSError):
            self.close()
            return None
        if latest is None:
            return None
        with Image.open(BytesIO(latest)) as image:
            return np.asarray(image.convert("RGB"))

    def close(self) -> None:
        """Terminate only the disposable worker process and release IPC handles."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._process is not None:
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=0.20)
                if self._process.is_alive():
                    self._process.kill()
            self._process = None
