"""ModernGL renderer for a frequency-bar spectrum."""

import moderngl
import numpy as np

from musicscope.scene.model import VisualState


class SpectrumRenderer:
    """Draw one coloured bar per audio frequency band."""

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        in vec3 in_color;
        out vec3 color;
        void main() {
            color = in_color;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        in vec3 color;
        out vec4 fragment_color;
        void main() {
            fragment_color = vec4(color, 1.0);
        }
    """

    def __init__(self, context: moderngl.Context, bar_count: int = 48) -> None:
        self._context = context
        self._bar_count = bar_count
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        self._buffer = context.buffer(reserve=bar_count * 6 * 5 * 4, dynamic=True)
        self._vertex_array = context.vertex_array(
            self._program,
            [(self._buffer, "2f 3f", "in_position", "in_color")],
        )

    def render(self, state: VisualState) -> None:
        """Upload and draw the current spectrum as clipped OpenGL triangles."""
        levels = state.spectrum or (0.0,) * self._bar_count
        levels = levels[: self._bar_count]
        if len(levels) < self._bar_count:
            levels = (*levels, *((0.0,) * (self._bar_count - len(levels))))
        self._buffer.write(self._vertices(levels))
        self._vertex_array.render(mode=moderngl.TRIANGLES, vertices=self._bar_count * 6)

    def _vertices(self, levels: tuple[float, ...]) -> bytes:
        width = 1.8 / self._bar_count
        gap = width * 0.16
        values: list[float] = []
        for index, level in enumerate(levels):
            left = -0.9 + index * width + gap / 2
            right = left + width - gap
            bottom = -0.82
            top = bottom + max(0.015, level * 1.58)
            ratio = index / max(self._bar_count - 1, 1)
            color = (0.2 + ratio * 0.7, 0.35 + level * 0.6, 1.0 - ratio * 0.55)
            corners = (
                (left, bottom),
                (right, bottom),
                (right, top),
                (left, bottom),
                (right, top),
                (left, top),
            )
            for x, y in corners:
                values.extend((x, y, *color))
        return np.asarray(values, dtype="f4").tobytes()
