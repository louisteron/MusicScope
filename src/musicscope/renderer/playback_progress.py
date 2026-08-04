"""Neon playback progress overlay for controllable local CD playback."""

from array import array

import moderngl
from PIL import Image, ImageDraw, ImageFont

from musicscope.renderer.color_settings import ColorSettings


class PlaybackProgressRenderer:
    """Draw a bottom progress rail and the current track time."""

    _SIZE = (1000, 110)
    _HORIZONTAL_HALF_WIDTH = 1.30

    def __init__(self, context: moderngl.Context, colors: ColorSettings) -> None:
        self._context = context
        self._colors = colors
        self._program = context.program(
            vertex_shader="""#version 330
                in vec2 position; in vec2 uv_in; out vec2 uv;
                uniform float aspect;
                void main() {
                    uv = uv_in;
                    gl_Position = vec4(position.x / aspect, position.y, 0.0, 1.0);
                }""",
            fragment_shader="""#version 330
                uniform sampler2D progress; uniform vec3 color; in vec2 uv;
                out vec4 fragment_color;
                void main() {
                    vec4 source = texture(progress, uv);
                    fragment_color = vec4(color * source.g, source.a);
                }""",
        )
        vertices = context.buffer(
            array(
                "f", (-1.30, -0.90, 0, 0, 1.30, -0.90, 1, 0, -1.30, -0.62, 0, 1, 1.30, -0.62, 1, 1)
            ).tobytes()
        )
        self._vao = context.vertex_array(self._program, [(vertices, "2f 2f", "position", "uv_in")])
        self._texture = context.texture(
            self._SIZE, 4, data=bytes(self._SIZE[0] * self._SIZE[1] * 4)
        )
        self._texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._last: tuple[float, float] | None = None

    def render(self, visible: bool, position: float, duration: float) -> None:
        """Render only while the user has opened the transport with Space."""
        if not visible:
            return
        values = (max(0.0, position), max(0.0, duration))
        if values != self._last:
            self._texture.write(
                self._image(*values).transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
            )
            self._last = values
        _, _, width, height = self._context.viewport
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self._texture.use(0)
        self._program["progress"].value = 0
        self._program["color"].value = self._colors.theme_color
        self._program["aspect"].value = width / height if height else 1.0
        self._vao.render(moderngl.TRIANGLE_STRIP)
        self._context.disable(moderngl.BLEND)

    def _image(self, position: float, duration: float) -> Image.Image:
        image = Image.new("RGBA", self._SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = self._font(30)
        ready = duration > 0
        fraction = min(1.0, position / duration) if ready else 0.0
        draw.rounded_rectangle((30, 35, 970, 63), radius=12, outline=(80, 255, 160, 225), width=3)
        draw.rounded_rectangle(
            (34, 39, 34 + 932 * fraction, 59), radius=8, fill=(80, 255, 160, 180)
        )
        knob_x = 34 + 932 * fraction
        draw.ellipse((knob_x - 10, 29, knob_x + 10, 69), outline=(160, 255, 205, 255), width=3)
        label = f"{self._time(position)} / {self._time(duration) if ready else '--:--'}"
        draw.text((30, 70), label, fill=(115, 255, 175, 255), font=font)
        draw.text((700, 70), "CLICK TO SEEK", fill=(70, 200, 130, 220), font=self._font(20))
        return image

    @staticmethod
    def _time(seconds: float) -> str:
        minutes, seconds = divmod(round(seconds), 60)
        return f"{minutes}:{seconds:02d}"

    @classmethod
    def fraction_from_cursor(
        cls,
        cursor_x: float,
        window_width: int,
        aspect_ratio: float,
    ) -> float:
        """Map a window cursor position to the visible progress rail."""
        if window_width <= 0 or aspect_ratio <= 0:
            return 0.0
        half_width = cls._HORIZONTAL_HALF_WIDTH / aspect_ratio
        left = (1.0 - half_width) * 0.5
        right = (1.0 + half_width) * 0.5
        position = cursor_x / window_width
        return max(0.0, min(1.0, (position - left) / (right - left)))

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype("DejaVuSansMono-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)
