"""Tests for platform-aware OpenCV camera opening."""

import sys

from musicscope import camera
from musicscope.camera import source
from musicscope.camera.source import OpenCvCameraSource


class _Capture:
    def __init__(self, opened: bool) -> None:
        self._opened = opened
        self.released = False
        self.properties: list[tuple[int, int]] = []

    def isOpened(self) -> bool:
        return self._opened

    def release(self) -> None:
        self.released = True

    def set(self, property_id: int, value: int) -> None:
        self.properties.append((property_id, value))


class _OpenCv:
    CAP_DSHOW = 700
    CAP_MSMF = 1400
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_FPS = 5
    CAP_PROP_BUFFERSIZE = 6

    def __init__(self, opened_indices: set[int]) -> None:
        self._opened_indices = opened_indices
        self.calls: list[tuple[int, ...]] = []
        self.captures: list[_Capture] = []

    def VideoCapture(self, *args: int) -> _Capture:
        self.calls.append(args)
        capture = _Capture(args[0] in self._opened_indices)
        self.captures.append(capture)
        return capture


def test_windows_camera_prefers_directshow(monkeypatch) -> None:
    cv2 = _OpenCv({1})
    monkeypatch.setattr(source.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "cv2", cv2)

    camera = OpenCvCameraSource(index=1)

    assert camera.open()
    assert cv2.calls == [(1, cv2.CAP_DSHOW)]
    assert cv2.captures[0].properties[-1] == (cv2.CAP_PROP_BUFFERSIZE, 1)


def test_camera_falls_back_to_primary_device(monkeypatch) -> None:
    cv2 = _OpenCv({0})
    monkeypatch.setattr(source.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "cv2", cv2)

    camera = OpenCvCameraSource(index=1)

    assert camera.open()
    assert cv2.calls[-1] == (0, cv2.CAP_DSHOW)
    assert all(capture.released for capture in cv2.captures[:-1])


def test_camera_source_uses_the_app_process_for_camera_permissions() -> None:
    assert isinstance(camera.create_camera_source(1), OpenCvCameraSource)
