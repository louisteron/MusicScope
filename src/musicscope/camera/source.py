"""Camera source implementations."""

import logging
from typing import Protocol

import numpy as np


class CameraFrameSource(Protocol):
    """Provide RGB frames without exposing a camera backend to renderers."""

    def open(self) -> bool: ...

    def read_frame(self) -> np.ndarray | None: ...

    def close(self) -> None: ...


class OpenCvCameraSource:
    """Read the selected webcam with OpenCV only while camera mode is active."""

    def __init__(self, index: int = 0, logger: logging.Logger | None = None) -> None:
        self._index = index
        self._logger = logger or logging.getLogger("musicscope")
        self._capture: object | None = None
        self._cv2: object | None = None

    def open(self) -> bool:
        """Open the camera and let the operating system request permission when needed."""
        try:
            import cv2
        except ImportError:
            self._logger.warning("Camera mode unavailable: OpenCV is not installed.")
            return False
        capture = cv2.VideoCapture(self._index)
        if not capture.isOpened():
            capture.release()
            self._logger.warning("Camera mode unavailable: no camera could be opened.")
            return False
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        capture.set(cv2.CAP_PROP_FPS, 30)
        self._cv2 = cv2
        self._capture = capture
        self._logger.info("Camera background started (camera %s).", self._index)
        return True

    def read_frame(self) -> np.ndarray | None:
        """Return a single RGB camera frame, or ``None`` while no frame is available."""
        if self._capture is None or self._cv2 is None:
            return None
        success, frame = self._capture.read()  # type: ignore[union-attr]
        if not success:
            return None
        return self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)  # type: ignore[union-attr]

    def close(self) -> None:
        """Release the camera device."""
        if self._capture is not None:
            self._capture.release()  # type: ignore[union-attr]
            self._capture = None
        self._cv2 = None
