"""Camera capture services used by visual backgrounds."""

import sys

from musicscope.camera.capture import CameraCapture
from musicscope.camera.isolated_source import IsolatedCameraSource
from musicscope.camera.source import OpenCvCameraSource


def create_camera_source(index: int, logger=None):
    """Choose crash isolation for macOS AVFoundation camera drivers."""
    if sys.platform == "darwin":
        return IsolatedCameraSource(index, logger=logger)
    return OpenCvCameraSource(index, logger=logger)


__all__ = ["CameraCapture", "OpenCvCameraSource", "create_camera_source"]
