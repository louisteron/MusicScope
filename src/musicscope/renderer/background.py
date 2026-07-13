"""The V0.1 audio-reactive background renderer."""

import moderngl

from musicscope.scene.model import VisualState


class BackgroundRenderer:
    """Clear a framebuffer using a colour derived from audio energy."""

    def __init__(self, context: moderngl.Context) -> None:
        self._context = context

    def render(self, state: VisualState, size: tuple[int, int]) -> None:
        """Render one frame at the supplied framebuffer size."""
        width, height = size
        energy = state.energy
        self._context.viewport = (0, 0, width, height)
        self._context.clear(0.025 + energy * 0.10, 0.035 + energy * 0.14, 0.12 + energy * 0.30, 1.0)
