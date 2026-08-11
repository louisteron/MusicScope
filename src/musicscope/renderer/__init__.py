"""OpenGL renderers."""

from musicscope.renderer.artwork import ArtworkRenderer
from musicscope.renderer.background import BackgroundRenderer
from musicscope.renderer.camera_background import CameraBackgroundRenderer
from musicscope.renderer.camera_settings import BackgroundMode, CameraSettings
from musicscope.renderer.color_settings import ColorMode, ColorSettings, PhosphorColor
from musicscope.renderer.crt import CrtRenderer
from musicscope.renderer.lyrics import LyricsRenderer
from musicscope.renderer.oscillation_settings import OscillationSettings
from musicscope.renderer.oscilloscope import OscilloscopeRenderer
from musicscope.renderer.playback_progress import PlaybackProgressRenderer
from musicscope.renderer.playlist_menu import PlaylistMenuRenderer
from musicscope.renderer.settings_menu import SettingsMenuRenderer
from musicscope.renderer.spectrum import SpectrumRenderer
from musicscope.renderer.track_info import TrackInfoRenderer
from musicscope.renderer.track_info_settings import LyricEntryEffect, TrackInfoSettings

__all__ = [
    "ArtworkRenderer",
    "BackgroundRenderer",
    "BackgroundMode",
    "CameraBackgroundRenderer",
    "CameraSettings",
    "ColorMode",
    "ColorSettings",
    "PhosphorColor",
    "CrtRenderer",
    "LyricsRenderer",
    "OscilloscopeRenderer",
    "PlaybackProgressRenderer",
    "PlaylistMenuRenderer",
    "OscillationSettings",
    "SpectrumRenderer",
    "SettingsMenuRenderer",
    "TrackInfoRenderer",
    "TrackInfoSettings",
    "LyricEntryEffect",
]
