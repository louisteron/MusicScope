"""ModernGL renderer for a contained live-camera background."""

from array import array

import moderngl
import numpy as np


class CameraBackgroundRenderer:
    """Upload the latest RGB camera frame and draw it behind phosphor overlays."""

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position; in vec2 in_uv; out vec2 uv;
        void main() { uv = in_uv; gl_Position = vec4(in_position, 0.0, 1.0); }
    """
    _FRAGMENT_SHADER = """
        #version 330
        uniform sampler2D u_camera; uniform float u_camera_aspect; uniform float u_view_aspect;
        in vec2 uv; out vec4 fragment_color;
        void main() {
            vec2 sample_uv = uv;
            if (u_view_aspect > u_camera_aspect) {
                sample_uv.y = 0.5 + (uv.y - 0.5) * u_camera_aspect / u_view_aspect;
            } else {
                sample_uv.x = 0.5 + (uv.x - 0.5) * u_view_aspect / u_camera_aspect;
            }
            fragment_color = vec4(texture(u_camera, sample_uv).rgb * 0.62, 1.0);
        }
    """

    def __init__(self, context: moderngl.Context) -> None:
        self._context = context
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        positions = array("f", (-1, -1, 0, 0, 1, -1, 1, 0, -1, 1, 0, 1, 1, 1, 1, 1))
        vertices = context.buffer(positions.tobytes())
        self._vertex_array = context.vertex_array(
            self._program,
            [(vertices, "2f 2f", "in_position", "in_uv")],
        )
        self._texture: moderngl.Texture | None = None
        self._size: tuple[int, int] | None = None
        self._frame_identity: int | None = None

    def render(self, frame: np.ndarray, viewport: tuple[int, int]) -> None:
        """Render a camera frame with a cover fit, preserving its proportions."""
        height, width = frame.shape[:2]
        size = (width, height)
        if self._texture is None or self._size != size:
            self._texture = self._context.texture(size, components=3)
            self._texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._size = size
            self._frame_identity = None
        if self._frame_identity != id(frame):
            self._texture.write(np.ascontiguousarray(frame[::-1]).tobytes())
            self._frame_identity = id(frame)
        self._texture.use(0)
        self._program["u_camera"].value = 0
        self._program["u_camera_aspect"].value = width / height
        view_width, view_height = viewport
        self._program["u_view_aspect"].value = view_width / view_height if view_height else 1.0
        self._vertex_array.render(moderngl.TRIANGLE_STRIP)
