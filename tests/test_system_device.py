"""Tests for selecting a system-audio loopback rather than a microphone."""

from musicscope.audio.system_device import SystemAudioDeviceSelector


def test_selector_prefers_a_known_loopback_device() -> None:
    devices = (
        {"name": "MacBook Microphone", "max_input_channels": 1, "default_samplerate": 44_100},
        {"name": "BlackHole 2ch", "max_input_channels": 2, "default_samplerate": 48_000},
    )
    device = SystemAudioDeviceSelector(lambda: devices).select()
    assert device is not None
    assert device.name == "BlackHole 2ch"
    assert device.channels == 2


def test_selector_never_falls_back_to_a_microphone() -> None:
    devices = (
        {"name": "MacBook Microphone", "max_input_channels": 1, "default_samplerate": 44_100},
    )
    assert SystemAudioDeviceSelector(lambda: devices).select() is None


def test_selector_accepts_a_user_selected_input_device() -> None:
    devices = (
        {"name": "Studio Loop Device", "max_input_channels": 4, "default_samplerate": 48_000},
    )
    device = SystemAudioDeviceSelector(lambda: devices).select("studio")
    assert device is not None
    assert device.channels == 2
