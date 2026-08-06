"""Audio input and signal analysis."""

from musicscope.audio.analyzer import AudioAnalyzer, AudioFrame
from musicscope.audio.cd_ejector import CdEjector
from musicscope.audio.cd_player import CdPlayer
from musicscope.audio.input import AudioInput
from musicscope.audio.local_artwork_service import LocalArtworkService
from musicscope.audio.local_metadata import LocalMetadataReader, LocalTrackInfo
from musicscope.audio.local_playlist import LocalPlaylist
from musicscope.audio.local_playlist_player import LocalPlaylistPlayer
from musicscope.audio.mpv_track_monitor import MpvTrackMonitor
from musicscope.audio.output import AudioOutput, AudioOutputDevice, AudioOutputDeviceSelector
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.audio.player_executable import resolve_mpv_executable
from musicscope.audio.system_device import SystemAudioDevice, SystemAudioDeviceSelector

__all__ = [
    "AudioAnalyzer",
    "AudioFrame",
    "CdEjector",
    "CdPlayer",
    "AudioInput",
    "LocalArtworkService",
    "LocalMetadataReader",
    "LocalTrackInfo",
    "LocalPlaylist",
    "LocalPlaylistPlayer",
    "MpvTrackMonitor",
    "resolve_mpv_executable",
    "AudioOutput",
    "AudioOutputDevice",
    "AudioOutputDeviceSelector",
    "AudioOutputSettings",
    "SystemAudioDevice",
    "SystemAudioDeviceSelector",
]
