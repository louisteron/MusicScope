"""OpenGL renderers."""

from musicscope.renderer.artwork import ArtworkRenderer
from musicscope.renderer.background import BackgroundRenderer
from musicscope.renderer.crt import CrtRenderer
from musicscope.renderer.oscilloscope import OscilloscopeRenderer
from musicscope.renderer.spectrum import SpectrumRenderer

__all__ = [
    "ArtworkRenderer",
    "BackgroundRenderer",
    "CrtRenderer",
    "OscilloscopeRenderer",
    "SpectrumRenderer",
]
