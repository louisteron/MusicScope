"""Tests for serialized live-camera source changes."""

from threading import Event

from musicscope.camera.capture import CameraCapture


class _Source:
    def __init__(self, name: str, events: list[str]) -> None:
        self._name = name
        self._events = events
        self.opened = Event()

    def open(self) -> bool:
        self._events.append(f"{self._name}:open")
        self.opened.set()
        return True

    def read_frame(self) -> None:
        return None

    def close(self) -> None:
        self._events.append(f"{self._name}:close")


def test_camera_source_replacement_closes_before_opening_the_next_source() -> None:
    events: list[str] = []
    first = _Source("first", events)
    second = _Source("second", events)
    capture = CameraCapture(first)

    capture.start()
    assert first.opened.wait(1)
    capture.replace_source(second)

    assert second.opened.wait(1)
    capture.stop()
    assert events.index("first:close") < events.index("second:open")
