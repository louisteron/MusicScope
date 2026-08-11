"""OpenGL overlay for the oscilloscope settings menu."""

from array import array

import moderngl
from PIL import Image, ImageDraw, ImageFont

from musicscope.renderer.color_settings import ColorSettings


class SettingsMenuRenderer:
    """Render a compact phosphor menu in the top-left corner."""

    _TEXTURE_SIZE = (1000, 560)
    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        in vec2 in_uv;
        uniform float u_aspect_ratio;
        out vec2 uv;
        void main() {
            uv = in_uv;
            gl_Position = vec4(in_position.x / u_aspect_ratio, in_position.y, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        uniform sampler2D u_menu;
        uniform vec3 u_theme_color;
        in vec2 uv;
        out vec4 fragment_color;
        void main() {
            vec4 source = texture(u_menu, uv);
            fragment_color = vec4(u_theme_color * source.g, source.a);
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
        vertices = array(
            "f",
            (
                -1.55,
                -0.35,
                0.0,
                0.0,
                1.40,
                -0.35,
                1.0,
                0.0,
                -1.55,
                0.94,
                0.0,
                1.0,
                1.40,
                0.94,
                1.0,
                1.0,
            ),
        )
        buffer = context.buffer(vertices.tobytes())
        self._vertex_array = context.vertex_array(
            self._program,
            [(buffer, "2f 2f", "in_position", "in_uv")],
        )
        self._texture = context.texture(
            self._TEXTURE_SIZE,
            components=4,
            data=bytes(self._TEXTURE_SIZE[0] * self._TEXTURE_SIZE[1] * 4),
        )
        self._texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._lines: tuple[tuple[str, ...], tuple[str, ...]] | None = None

    def render(
        self,
        visible: bool,
        visual_lines: tuple[str, ...],
        audio_lines: tuple[str, ...],
    ) -> None:
        """Draw the menu only while it is open."""
        if not visible:
            return
        lines = (visual_lines, audio_lines)
        if lines != self._lines:
            bitmap = self._menu_image(*lines).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            self._texture.write(bitmap.tobytes())
            self._lines = lines
        _, _, width, height = self._context.viewport
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self._texture.use(location=0)
        self._program["u_menu"].value = 0
        self._program["u_aspect_ratio"].value = width / height if height else 1.0
        self._program["u_theme_color"].value = self._color_settings.theme_color
        self._vertex_array.render(mode=moderngl.TRIANGLE_STRIP)
        self._context.disable(moderngl.BLEND)

    def _menu_image(
        self,
        visual_lines: tuple[str, ...],
        audio_lines: tuple[str, ...],
    ) -> Image.Image:
        image = Image.new("RGBA", self._TEXTURE_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        visual_panel = (8, 8, 480, 558)
        audio_panel = (520, 8, 992, 310)
        draw.rounded_rectangle(visual_panel, radius=12, fill=(0, 12, 4, 205))
        draw.rounded_rectangle(audio_panel, radius=12, fill=(0, 12, 4, 205))
        draw.rounded_rectangle(visual_panel, radius=12, outline=(45, 255, 125, 210), width=4)
        draw.rounded_rectangle(audio_panel, radius=12, outline=(45, 255, 125, 210), width=4)
        font = self._font(28)
        heading_font = self._font(24)
        draw.text((32, 20), "VISUAL", fill=(75, 255, 145, 255), font=heading_font)
        draw.text((530, 20), "AUDIO", fill=(75, 255, 145, 255), font=heading_font)
        self._draw_column(draw, visual_lines, 32, font)
        self._draw_column(draw, audio_lines, 530, font)
        draw.text(
            (32, 528),
            "M CLOSE",
            fill=(45, 190, 100, 220),
            font=self._font(18),
        )
        draw.text(
            (530, 266),
            "ARROWS ADJUST",
            fill=(45, 190, 100, 220),
            font=self._font(18),
        )
        return image

    @staticmethod
    def _draw_column(
        draw: ImageDraw.ImageDraw,
        lines: tuple[str, ...],
        x: int,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> None:
        for index, line in enumerate(lines):
            color = (100, 255, 155, 255) if line.startswith(">") else (45, 190, 100, 255)
            draw.text((x, 78 + index * 40), line, fill=color, font=font)

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype("DejaVuSansMono-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)
