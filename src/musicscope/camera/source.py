"""Camera source implementations."""

import logging
import sys
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
        for device_index in self._device_indices():
            for backend, backend_name in self._backends(cv2):
                capture = self._open_capture(cv2, device_index, backend)
                if not capture.isOpened():
                    capture.release()
                    continue
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                capture.set(cv2.CAP_PROP_FPS, 30)
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self._cv2 = cv2
                self._capture = capture
                self._logger.info(
                    "Camera background started (camera %s, %s).",
                    device_index,
                    backend_name,
                )
                return True
        self._logger.warning(
            "Camera mode unavailable: no camera could be opened (requested camera %s).",
            self._index,
        )
        return False

    def _device_indices(self) -> tuple[int, ...]:
        """Try the requested device first, then the usual primary webcam."""
        return (self._index, 0) if self._index else (0,)

    @staticmethod
    def _backends(cv2: object) -> tuple[tuple[int | None, str], ...]:
        """Return capture backends ordered for the active operating system."""
        if sys.platform != "win32":
            return ((None, "default backend"),)
        candidates = (
            (getattr(cv2, "CAP_DSHOW", None), "DirectShow"),
            (getattr(cv2, "CAP_MSMF", None), "Media Foundation"),
            (None, "default backend"),
        )
        return candidates

    @staticmethod
    def _open_capture(cv2: object, index: int, backend: int | None) -> object:
        """Create one capture instance while allowing OpenCV backend fallbacks."""
        if backend is None:
            return cv2.VideoCapture(index)  # type: ignore[union-attr]
        return cv2.VideoCapture(index, backend)  # type: ignore[union-attr]

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
