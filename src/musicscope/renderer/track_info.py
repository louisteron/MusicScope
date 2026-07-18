"""Neon track metadata renderer, independent from recognition providers."""

from array import array

import moderngl
from PIL import Image, ImageDraw, ImageFont

from musicscope.renderer.color_settings import ColorSettings
from musicscope.scene.model import VisualState


class TrackInfoRenderer:
    """Render the scene's current title and artist in a phosphor-style label."""

    _TEXTURE_SIZE = (1024, 180)
    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        in vec2 in_uv;
        out vec2 uv;
        void main() {
            uv = in_uv;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        uniform sampler2D u_label;
        uniform float u_opacity;
        uniform vec3 u_theme_color;
        in vec2 uv;
        out vec4 fragment_color;
        void main() {
            float mask = texture(u_label, uv).r;
            fragment_color = vec4(u_theme_color, mask * u_opacity);
        }
    """

    def __init__(
        self,
        context: moderngl.Context,
        color_settings: ColorSettings | None = None,
    ) -> None:
        self._context = context
        self._color_settings = color_settings or ColorSettings()
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        vertices = context.buffer(
            data=array(
                "f",
                (
                -0.58,
                -0.60,
                0.0,
                0.0,
                0.58,
                -0.60,
                1.0,
                0.0,
                -0.58,
                -0.42,
                0.0,
                1.0,
                0.58,
                -0.42,
                1.0,
                1.0,
                ),
            ).tobytes()
        )
        self._vertex_array = context.vertex_array(
            self._program,
            [(vertices, "2f 2f", "in_position", "in_uv")],
        )
        self._texture = context.texture(self._TEXTURE_SIZE, components=1, data=bytes(1024 * 180))
        self._texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._label: str | None = None

    def render(self, state: VisualState) -> None:
        """Draw the latest recognized metadata, if the scene has any."""
        label = self._label_for(state)
        if label is None:
            return
        if label != self._label:
            bitmap = self._label_image(label).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            self._texture.write(bitmap.tobytes())
            self._label = label
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self._texture.use(location=0)
        self._program["u_label"].value = 0
        self._program["u_theme_color"].value = self._color_settings.theme_color
        for opacity in (0.08, 0.20, 0.88):
            self._program["u_opacity"].value = opacity
            self._vertex_array.render(mode=moderngl.TRIANGLE_STRIP)
        self._context.disable(moderngl.BLEND)

    @staticmethod
    def _label_for(state: VisualState) -> str | None:
        if not state.track_title or not state.artist_name:
            return None
        title = state.track_title.upper()[:48]
        artist = state.artist_name.upper()[:56]
        return f"{title}\n{artist}"

    def _label_image(self, label: str) -> Image.Image:
        image = Image.new("L", self._TEXTURE_SIZE)
        draw = ImageDraw.Draw(image)
        title, artist = label.split("\n", maxsplit=1)
        self._draw_centered(draw, title, y=24, font=self._font(54))
        self._draw_centered(draw, artist, y=100, font=self._font(34))
        return image

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype("DejaVuSansMono-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)

    def _draw_centered(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> None:
        bounds = draw.textbbox((0, 0), text, font=font)
        width = bounds[2] - bounds[0]
        draw.text(((self._TEXTURE_SIZE[0] - width) // 2, y), text, fill=255, font=font)
