"""OpenGL renderers."""

from musicscope.renderer.artwork import ArtworkRenderer
from musicscope.renderer.background import BackgroundRenderer
from musicscope.renderer.color_settings import ColorMode, ColorSettings
from musicscope.renderer.crt import CrtRenderer
from musicscope.renderer.oscillation_settings import OscillationSettings
from musicscope.renderer.oscilloscope import OscilloscopeRenderer
from musicscope.renderer.settings_menu import SettingsMenuRenderer
from musicscope.renderer.spectrum import SpectrumRenderer
from musicscope.renderer.track_info import TrackInfoRenderer

__all__ = [
    "ArtworkRenderer",
    "BackgroundRenderer",
    "ColorMode",
    "ColorSettings",
    "CrtRenderer",
    "OscilloscopeRenderer",
    "OscillationSettings",
    "SpectrumRenderer",
    "SettingsMenuRenderer",
    "TrackInfoRenderer",
]
