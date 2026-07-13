"""Audio input and signal analysis."""

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame
from musicscope.audio.input import AudioInput
from musicscope.audio.system_device import SystemAudioDevice, SystemAudioDeviceSelector

__all__ = [
    "AudioAnalyzer",
    "AudioFrame",
    "AudioInput",
    "SystemAudioDevice",
    "SystemAudioDeviceSelector",
]
