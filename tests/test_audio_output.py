"""Tests for selectable audio monitoring outputs."""

from musicscope.audio.output import AudioOutputDeviceSelector
from musicscope.audio.output_settings import AudioOutputSettings


def test_output_selector_lists_playback_devices() -> None:
    devices = (
        {"name": "Line Input", "max_output_channels": 0},
        {"name": "Headphones / Jack", "max_output_channels": 2},
    )

    outputs = AudioOutputDeviceSelector(lambda: devices).available()

    assert len(outputs) == 1
    assert outputs[0].name == "Headphones / Jack"


def test_output_settings_cycles_from_off_to_first_device() -> None:
    output = AudioOutputSettings(AudioOutputDeviceSelector(lambda: (
        {"name": "Hi-Fi", "max_output_channels": 2},
    )).available())

    output.cycle(1)

    assert output.label == "HI-FI"
