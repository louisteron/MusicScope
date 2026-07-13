"""Tests for scene state transitions."""

from musicscope.audio.analyzer import AudioFrame
from musicscope.scene.manager import SceneManager


def test_scene_manager_smooths_audio_energy() -> None:
    manager = SceneManager()
    manager.update_audio(AudioFrame(volume=1.0, spectrum=(1.0, 0.0)))
    assert manager.state.energy == 0.2
    assert manager.state.spectrum == (1.0, 0.0)
