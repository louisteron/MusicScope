"""Tests for scene state transitions."""

from musicscope.audio.analyzer import AudioFrame
from musicscope.scene.manager import SceneManager


def test_scene_manager_smooths_audio_energy() -> None:
    manager = SceneManager()
    manager.update_audio(AudioFrame(volume=1.0, spectrum=(1.0, 0.0), waveform=(0.3, -0.3)))
    assert manager.state.energy == 0.45
    assert manager.state.spectrum == (1.0, 0.0)
    assert manager.state.waveform == (0.3, -0.3)


def test_scene_manager_keeps_track_metadata_during_audio_updates() -> None:
    manager = SceneManager()
    manager.set_track("Song", "Artist", "/tmp/cover.jpg")
    manager.update_audio(AudioFrame(volume=0.1, waveform=(0.1,)))
    assert manager.state.track_title == "Song"
    assert manager.state.artwork_path == "/tmp/cover.jpg"


def test_scene_manager_releases_energy_gradually_after_audio_stops() -> None:
    manager = SceneManager()
    manager.update_audio(AudioFrame(volume=1.0, waveform=(1.0, -1.0)))
    manager.update_audio(AudioFrame(volume=0.0, waveform=(0.0, 0.0)))
    assert manager.state.energy > 0.19
    assert manager.state.waveform != (0.0, 0.0)
