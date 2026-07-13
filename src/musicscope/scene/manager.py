"""Owns the active scene's visual state."""

from threading import Lock

from musicscope.audio.analyzer import AudioFrame
from musicscope.scene.model import VisualState


class SceneManager:
    """Translate audio frames into a state usable by a renderer."""

    def __init__(self) -> None:
        self._state = VisualState()
        self._lock = Lock()

    @property
    def state(self) -> VisualState:
        """Return the most recently calculated visual state."""
        with self._lock:
            return self._state

    def update_audio(self, frame: AudioFrame) -> None:
        """Apply a simple temporal smoothing to incoming audio energy."""
        with self._lock:
            energy = self._state.energy * 0.8 + frame.volume * 0.2
            previous = self._state.spectrum
            spectrum = tuple(
                old * 0.65 + new * 0.35
                for old, new in zip(previous, frame.spectrum, strict=True)
            ) if previous else frame.spectrum
            self._state = VisualState(energy=energy, spectrum=spectrum)
