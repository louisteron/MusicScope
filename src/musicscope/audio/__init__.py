"""Audio input and signal analysis."""

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame
from musicscope.audio.input import AudioInput
from musicscope.audio.output import AudioOutput, AudioOutputDevice, AudioOutputDeviceSelector
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.audio.system_device import SystemAudioDevice, SystemAudioDeviceSelector

__all__ = [
    "AudioAnalyzer",
    "AudioFrame",
    "AudioInput",
    "AudioOutput",
    "AudioOutputDevice",
    "AudioOutputDeviceSelector",
    "AudioOutputSettings",
    "SystemAudioDevice",
    "SystemAudioDeviceSelector",
]
