"""Audio input and signal analysis."""

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame
from musicscope.audio.cd_ejector import CdEjector
from musicscope.audio.cd_player import CdPlayer
from musicscope.audio.input import AudioInput
from musicscope.audio.mpv_track_monitor import MpvTrackMonitor
from musicscope.audio.output import AudioOutput, AudioOutputDevice, AudioOutputDeviceSelector
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.audio.system_device import SystemAudioDevice, SystemAudioDeviceSelector

__all__ = [
    "AudioAnalyzer",
    "AudioFrame",
    "CdEjector",
    "CdPlayer",
    "AudioInput",
    "MpvTrackMonitor",
    "AudioOutput",
    "AudioOutputDevice",
    "AudioOutputDeviceSelector",
    "AudioOutputSettings",
    "SystemAudioDevice",
    "SystemAudioDeviceSelector",
]
