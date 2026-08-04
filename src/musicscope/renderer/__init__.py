"""OpenGL renderers."""

from musicscope.renderer.artwork import ArtworkRenderer
from musicscope.renderer.background import BackgroundRenderer
from musicscope.renderer.color_settings import ColorMode, ColorSettings, PhosphorColor
from musicscope.renderer.crt import CrtRenderer
from musicscope.renderer.lyrics import LyricsRenderer
from musicscope.renderer.oscillation_settings import OscillationSettings
from musicscope.renderer.oscilloscope import OscilloscopeRenderer
from musicscope.renderer.playback_progress import PlaybackProgressRenderer
from musicscope.renderer.settings_menu import SettingsMenuRenderer
from musicscope.renderer.spectrum import SpectrumRenderer
from musicscope.renderer.track_info import TrackInfoRenderer
from musicscope.renderer.track_info_settings import LyricEntryEffect, TrackInfoSettings

__all__ = [
    "ArtworkRenderer",
    "BackgroundRenderer",
    "ColorMode",
    "ColorSettings",
    "PhosphorColor",
    "CrtRenderer",
    "LyricsRenderer",
    "OscilloscopeRenderer",
    "PlaybackProgressRenderer",
    "OscillationSettings",
    "SpectrumRenderer",
    "SettingsMenuRenderer",
    "TrackInfoRenderer",
    "TrackInfoSettings",
    "LyricEntryEffect",
]
