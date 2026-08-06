"""OpenGL side panel displaying and editing the local audio playlist."""

from array import array

import moderngl
from PIL import Image, ImageDraw, ImageFont

from musicscope.audio.local_playlist import LocalPlaylist
from musicscope.renderer.color_settings import ColorSettings


class PlaylistMenuRenderer:
    """Draw a right-side playlist panel without owning playlist state."""

    _TEXTURE_SIZE = (760, 1000)
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
                0.18, -0.86, 0.0, 0.0,
                0.98, -0.86, 1.0, 0.0,
                0.18, 0.88, 0.0, 1.0,
                0.98, 0.88, 1.0, 1.0,
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
        self._content: tuple[tuple[tuple[int, str], ...], int | None, int | None] | None = None

    def render(
        self,
        visible: bool,
        playlist: LocalPlaylist,
        current_index: int | None,
        dragging_index: int | None,
        max_visible_tracks: int,
        offset: int,
    ) -> None:
        """Draw the panel and its first visible playlist rows."""
        if not visible:
            return
        entries = self._entries(playlist, max_visible_tracks, offset)
        content = (entries, current_index, dragging_index)
        if content != self._content:
            bitmap = self._image(*content).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            self._texture.write(bitmap.tobytes())
            self._content = content
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self._texture.use(location=0)
        self._program["u_menu"].value = 0
        self._program["u_theme_color"].value = self._color_settings.theme_color
        self._vertex_array.render(mode=moderngl.TRIANGLE_STRIP)
        self._context.disable(moderngl.BLEND)

    def _image(
        self,
        entries: tuple[tuple[int, str], ...],
        current_index: int | None,
        dragging_index: int | None,
    ) -> Image.Image:
        image = Image.new("RGBA", self._TEXTURE_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        panel = (8, 8, 752, 992)
        draw.rounded_rectangle(panel, radius=16, fill=(0, 12, 4, 220))
        draw.rounded_rectangle(panel, radius=16, outline=(45, 255, 125, 220), width=4)
        draw.text((40, 28), "PLAYLIST", fill=(75, 255, 145, 255), font=self._font(34))
        draw.text(
            (40, 78),
            "P CLOSE  •  CLICK PLAY  •  DRAG REORDER  •  UP/DOWN SCROLL",
            fill=(45, 190, 100, 230),
            font=self._font(18),
        )
        if not entries:
            draw.text(
                (40, 190),
                "DROP AUDIO FILES OR A FOLDER HERE",
                fill=(45, 190, 100, 255),
                font=self._font(22),
            )
        for row, (index, entry) in enumerate(entries):
            top = 170 + row * 61
            selected = index == current_index
            dragging = index == dragging_index
            if selected or dragging:
                draw.rounded_rectangle(
                    (24, top, 736, top + 52),
                    radius=8,
                    fill=(18, 82, 40, 190),
                )
            color = (120, 255, 175, 255) if selected else (65, 220, 120, 255)
            draw.text((42, top + 12), entry, fill=color, font=self._font(20))
            draw.text((690, top + 12), "×", fill=(120, 255, 175, 255), font=self._font(28))
        if playlist_size := len(entries):
            draw.text(
                (40, 828),
                f"{playlist_size} TRACK(S) VISIBLE",
                fill=(45, 190, 100, 230),
                font=self._font(18),
            )
        draw.rounded_rectangle((28, 880, 732, 956), radius=10, outline=(70, 220, 120, 230), width=2)
        draw.text((236, 900), "CLEAR PLAYLIST", fill=(100, 255, 155, 255), font=self._font(25))
        return image

    @staticmethod
    def _entries(
        playlist: LocalPlaylist,
        maximum: int,
        offset: int,
    ) -> tuple[tuple[int, str], ...]:
        entries: list[tuple[int, str]] = []
        for index in range(offset + 1, min(playlist.size, offset + maximum) + 1):
            track = playlist.track_at(index)
            if track is None:
                continue
            entry = f"{index:02d}  {track.artist} — {track.title}"
            entries.append((index, entry[:48]))
        return tuple(entries)

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype("DejaVuSansMono-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)
