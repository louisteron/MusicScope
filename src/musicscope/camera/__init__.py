"""Camera capture services used by visual backgrounds."""

from musicscope.camera.capture import CameraCapture
from musicscope.camera.source import OpenCvCameraSource


def create_camera_source(index: int, logger=None):
    """Create the source in the app process so macOS camera permissions apply."""
    return OpenCvCameraSource(index, logger=logger)


__all__ = ["CameraCapture", "OpenCvCameraSource", "create_camera_source"]
