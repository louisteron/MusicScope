"""Small neon renderer for the active synchronized lyric line."""

import unicodedata
from array import array

import moderngl
from PIL import Image, ImageDraw, ImageFont

from musicscope.renderer.color_settings import ColorSettings
from musicscope.renderer.track_info_settings import TrackInfoSettings
from musicscope.scene.model import VisualState


class LyricsRenderer:
    """Render one timed lyric line as a tall, hollow oscilloscope trace."""

    # A deliberately simple single-stroke alphabet, inspired by the vector
    # lettering used by Asteroids and early oscilloscope terminals.
    _GLYPHS: dict[str, tuple[tuple[float, float, float, float], ...]] = {
        "A": ((0, 1, 0.5, 0), (0.5, 0, 1, 1), (0.2, 0.58, 0.8, 0.58)),
        "B": (
            (0, 0, 0, 1),
            (0, 0, 0.72, 0.18),
            (0.72, 0.18, 0, 0.5),
            (0, 0.5, 0.72, 0.72),
            (0.72, 0.72, 0, 1),
        ),
        "C": (
            (0.92, 0.12, 0.68, 0),
            (0.68, 0, 0.15, 0.12),
            (0.15, 0.12, 0, 0.5),
            (0, 0.5, 0.15, 0.88),
            (0.15, 0.88, 0.68, 1),
            (0.68, 1, 0.92, 0.88),
        ),
        "D": (
            (0, 0, 0, 1),
            (0, 0, 0.55, 0.08),
            (0.55, 0.08, 0.88, 0.5),
            (0.88, 0.5, 0.55, 0.92),
            (0.55, 0.92, 0, 1),
        ),
        "E": ((0.92, 0, 0, 0), (0, 0, 0, 1), (0, 0.5, 0.7, 0.5), (0, 1, 0.92, 1)),
        "F": ((0, 1, 0, 0), (0, 0, 0.92, 0), (0, 0.5, 0.7, 0.5)),
        "G": (
            (0.92, 0.15, 0.68, 0),
            (0.68, 0, 0.15, 0.12),
            (0.15, 0.12, 0, 0.5),
            (0, 0.5, 0.15, 0.88),
            (0.15, 0.88, 0.7, 1),
            (0.7, 1, 0.92, 0.82),
            (0.92, 0.82, 0.92, 0.52),
            (0.92, 0.52, 0.48, 0.52),
        ),
        "H": ((0, 0, 0, 1), (1, 0, 1, 1), (0, 0.5, 1, 0.5)),
        "I": ((0, 0, 1, 0), (0.5, 0, 0.5, 1), (0, 1, 1, 1)),
        "J": ((0.12, 0, 1, 0), (0.72, 0, 0.72, 0.82), (0.72, 0.82, 0.48, 1), (0.48, 1, 0.12, 0.84)),
        "K": ((0, 0, 0, 1), (1, 0, 0, 0.52), (0, 0.52, 1, 1)),
        "L": ((0, 0, 0, 1), (0, 1, 0.95, 1)),
        "M": ((0, 1, 0, 0), (0, 0, 0.5, 0.48), (0.5, 0.48, 1, 0), (1, 0, 1, 1)),
        "N": ((0, 1, 0, 0), (0, 0, 1, 1), (1, 1, 1, 0)),
        "O": (
            (0.16, 0, 0.84, 0),
            (0.84, 0, 1, 0.18),
            (1, 0.18, 1, 0.82),
            (1, 0.82, 0.84, 1),
            (0.84, 1, 0.16, 1),
            (0.16, 1, 0, 0.82),
            (0, 0.82, 0, 0.18),
            (0, 0.18, 0.16, 0),
        ),
        "P": ((0, 1, 0, 0), (0, 0, 0.75, 0.12), (0.75, 0.12, 0.75, 0.42), (0.75, 0.42, 0, 0.52)),
        "Q": (
            (0.16, 0, 0.84, 0),
            (0.84, 0, 1, 0.18),
            (1, 0.18, 1, 0.82),
            (1, 0.82, 0.84, 1),
            (0.84, 1, 0.16, 1),
            (0.16, 1, 0, 0.82),
            (0, 0.82, 0, 0.18),
            (0, 0.18, 0.16, 0),
            (0.55, 0.58, 1.08, 1.08),
        ),
        "R": (
            (0, 1, 0, 0),
            (0, 0, 0.75, 0.12),
            (0.75, 0.12, 0.75, 0.42),
            (0.75, 0.42, 0, 0.52),
            (0.38, 0.52, 1, 1),
        ),
        "S": (
            (0.9, 0.14, 0.7, 0),
            (0.7, 0, 0.2, 0.08),
            (0.2, 0.08, 0, 0.4),
            (0, 0.4, 0.82, 0.6),
            (0.82, 0.6, 1, 0.88),
            (1, 0.88, 0.78, 1),
            (0.78, 1, 0.2, 0.92),
            (0.2, 0.92, 0.04, 0.8),
        ),
        "T": ((0, 0, 1, 0), (0.5, 0, 0.5, 1)),
        "U": (
            (0, 0, 0, 0.8),
            (0, 0.8, 0.22, 1),
            (0.22, 1, 0.78, 1),
            (0.78, 1, 1, 0.8),
            (1, 0.8, 1, 0),
        ),
        "V": ((0, 0, 0.5, 1), (0.5, 1, 1, 0)),
        "W": ((0, 0, 0.22, 1), (0.22, 1, 0.5, 0.48), (0.5, 0.48, 0.78, 1), (0.78, 1, 1, 0)),
        "X": ((0, 0, 1, 1), (1, 0, 0, 1)),
        "Y": ((0, 0, 0.5, 0.5), (1, 0, 0.5, 0.5), (0.5, 0.5, 0.5, 1)),
        "Z": ((0, 0, 1, 0), (1, 0, 0, 1), (0, 1, 1, 1)),
        "0": (
            (0.15, 0, 0.85, 0),
            (0.85, 0, 1, 0.15),
            (1, 0.15, 1, 0.85),
            (1, 0.85, 0.85, 1),
            (0.85, 1, 0.15, 1),
            (0.15, 1, 0, 0.85),
            (0, 0.85, 0, 0.15),
            (0, 0.15, 0.15, 0),
        ),
        "1": ((0.25, 0.2, 0.5, 0), (0.5, 0, 0.5, 1), (0.2, 1, 0.8, 1)),
        "2": (
            (0, 0.15, 0.2, 0),
            (0.2, 0, 0.8, 0),
            (0.8, 0, 1, 0.22),
            (1, 0.22, 0, 1),
            (0, 1, 1, 1),
        ),
        "3": (
            (0, 0.08, 0.8, 0),
            (0.8, 0, 1, 0.5),
            (1, 0.5, 0.8, 1),
            (0.8, 1, 0, 0.92),
            (0.25, 0.5, 0.85, 0.5),
        ),
        "4": ((0.85, 1, 0.85, 0), (0.85, 0, 0, 0.65), (0, 0.65, 1, 0.65)),
        "5": (
            (1, 0, 0.1, 0),
            (0.1, 0, 0, 0.5),
            (0, 0.5, 0.78, 0.5),
            (0.78, 0.5, 1, 0.7),
            (1, 0.7, 0.8, 1),
            (0.8, 1, 0.05, 1),
        ),
        "6": (
            (0.9, 0.1, 0.7, 0),
            (0.7, 0, 0.1, 0.2),
            (0.1, 0.2, 0, 0.8),
            (0, 0.8, 0.2, 1),
            (0.2, 1, 0.8, 1),
            (0.8, 1, 1, 0.72),
            (1, 0.72, 0.78, 0.5),
            (0.78, 0.5, 0, 0.5),
        ),
        "7": ((0, 0, 1, 0), (1, 0, 0.35, 1)),
        "8": (
            (0.18, 0, 0.82, 0),
            (0.82, 0, 1, 0.2),
            (1, 0.2, 0, 0.8),
            (0, 0.8, 0.18, 1),
            (0.18, 1, 0.82, 1),
            (0.82, 1, 1, 0.8),
            (1, 0.8, 0, 0.2),
            (0, 0.2, 0.18, 0),
        ),
        "9": (
            (1, 0.5, 0.22, 0.5),
            (0.22, 0.5, 0, 0.28),
            (0, 0.28, 0.2, 0),
            (0.2, 0, 0.8, 0),
            (0.8, 0, 1, 0.22),
            (1, 0.22, 1, 0.82),
            (1, 0.82, 0.78, 1),
            (0.78, 1, 0.1, 1),
        ),
        "-": ((0.15, 0.5, 0.85, 0.5),),
        "/": ((0, 1, 1, 0),),
        ".": ((0.45, 0.92, 0.55, 1),),
        "'": ((0.48, 0, 0.4, 0.2),),
        "!": ((0.5, 0, 0.5, 0.72), (0.5, 0.92, 0.5, 1)),
        "?": (
            (0, 0.15, 0.2, 0),
            (0.2, 0, 0.8, 0),
            (0.8, 0, 1, 0.2),
            (1, 0.2, 0.5, 0.55),
            (0.5, 0.72, 0.5, 0.75),
            (0.5, 0.94, 0.5, 1),
        ),
    }

    def __init__(
        self,
        context: moderngl.Context,
        color_settings: ColorSettings,
        track_info_settings: TrackInfoSettings | None = None,
    ) -> None:
        self._context = context
        self._colors = color_settings
        self._track_info_settings = track_info_settings or TrackInfoSettings()
        self._program = context.program(
            vertex_shader="""#version 330
                in vec2 position; in vec2 uv_in; out vec2 uv;
                void main() { uv = uv_in; gl_Position = vec4(position, 0.0, 1.0); }""",
            fragment_shader="""#version 330
                uniform sampler2D label;
                uniform vec3 color;
                uniform float bass;
                uniform float opacity;
                uniform float morph;
                uniform float time;
                in vec2 uv;
                out vec4 fragment_color;
                void main() {
                    vec2 from_center = uv - vec2(0.5);
                    float distance = length(from_center);
                    vec2 direction = normalize(from_center + vec2(0.0001));
                    float shockwave = sin(distance * 76.0 - time * 16.0)
                        * bass * 0.0035;
                    vec2 sample_uv = clamp(
                        uv + direction * shockwave, vec2(0.001), vec2(0.999)
                    );
                    vec2 glyph_uv = sample_uv;
                    glyph_uv.y = 0.5 + (sample_uv.y - 0.5) / max(morph, 0.08);
                    float within_glyph_band = (glyph_uv.y >= 0.0 && glyph_uv.y <= 1.0)
                        ? 1.0 : 0.0;
                    float mask = texture(label, clamp(glyph_uv, 0.001, 0.999)).r
                        * within_glyph_band;
                    float halo = (
                        texture(label, sample_uv + vec2(0.0025, 0.0)).r
                        + texture(label, sample_uv - vec2(0.0025, 0.0)).r
                        + texture(label, sample_uv + vec2(0.0, 0.006)).r
                        + texture(label, sample_uv - vec2(0.0, 0.006)).r
                    ) * 0.25;
                    fragment_color = vec4(
                        color * (0.65 + mask * 0.75),
                        max(mask, halo * 0.42) * opacity
                    );
                }""",
        )
        vertices = context.buffer(
            array(
                "f",
                (-0.82, -0.50, 0, 0, 0.82, -0.50, 1, 0, -0.82, 0.50, 0, 1, 0.82, 0.50, 1, 1),
            ).tobytes()
        )
        self._vao = context.vertex_array(self._program, [(vertices, "2f 2f", "position", "uv_in")])
        self._texture = context.texture((1024, 420), 1, data=bytes(1024 * 420))
        self._texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._line: str | None = None

    def render(self, state: VisualState, elapsed: float) -> None:
        """Draw the active lyric when synchronized lyrics are available."""
        if not self._track_info_settings.lyrics_wave or not state.lyric_line:
            return
        if state.lyric_line != self._line:
            image = Image.new("L", (1024, 420))
            draw = ImageDraw.Draw(image)
            lines, font = self._layout(draw, self._normalise_text(state.lyric_line))
            line_height = round(getattr(font, "size", 32) * 1.10)
            line_gap = max(6, getattr(font, "size", 32) // 9)
            block_height = line_height * len(lines) + line_gap * (len(lines) - 1)
            top = (420 - block_height) // 2
            for index, line in enumerate(lines):
                size = getattr(font, "size", 32)
                x = (1024 - self._vector_width(line, size)) / 2
                y = top + index * (line_height + line_gap)
                self._draw_vector_line(draw, line, x, y, size)
            self._texture.write(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())
            self._line = state.lyric_line
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self._texture.use(0)
        self._program["label"].value = 0
        self._program["color"].value = self._colors.theme_color
        self._program["bass"].value = (
            self._bass_motion(state.bass_energy)
            if self._track_info_settings.lyrics_reactive
            else 0.0
        )
        self._program["opacity"].value = state.lyric_opacity
        self._program["morph"].value = state.lyric_morph
        self._program["time"].value = elapsed
        self._vao.render(moderngl.TRIANGLE_STRIP)
        self._context.disable(moderngl.BLEND)

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype("DejaVuSansMono.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)

    def _layout(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
    ) -> tuple[tuple[str, ...], ImageFont.FreeTypeFont | ImageFont.ImageFont]:
        """Fit every word in up to three centred oscilloscope lines."""
        for size in range(132, 7, -2):
            font = self._font(size)
            lines = self._wrap_vector(text, size)
            line_gap = max(6, size // 9)
            block_height = round(size * 1.10) * len(lines) + line_gap * (len(lines) - 1)
            if (
                len(lines) <= 3
                and all(self._vector_width(line, size) <= 900 for line in lines)
                and block_height <= 360
            ):
                return lines, font
        font = self._font(8)
        return (text,), font

    @classmethod
    def _wrap_vector(
        cls,
        text: str,
        size: int,
        maximum_width: int = 900,
    ) -> tuple[str, ...]:
        """Wrap using the actual advance of the oscilloscope-vector glyphs."""
        lines: list[str] = []
        line = ""
        for word in text.split():
            candidate = f"{line} {word}".strip()
            if line and cls._vector_width(candidate, size) > maximum_width:
                lines.append(line)
                line = ""
            line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        return tuple(lines) or ("…",)

    @staticmethod
    def _wrap(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        maximum_width: int = 900,
    ) -> tuple[str, ...]:
        """Wrap complete words without silently dropping the end of a lyric."""
        lines: list[str] = []
        line = ""
        for word in text.split():
            if draw.textbbox((0, 0), word, font=font)[2] > maximum_width:
                if line:
                    lines.append(line)
                    line = ""
                remaining = word
                while remaining:
                    chunk_length = len(remaining)
                    while (
                        chunk_length > 1
                        and draw.textbbox((0, 0), remaining[:chunk_length], font=font)[2]
                        > maximum_width
                    ):
                        chunk_length -= 1
                    lines.append(remaining[:chunk_length])
                    remaining = remaining[chunk_length:]
                continue
            candidate = f"{line} {word}".strip()
            width = draw.textbbox((0, 0), candidate, font=font)[2]
            if line and width > maximum_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return tuple(lines) or ("…",)

    @staticmethod
    def _bass_motion(bass_energy: float) -> float:
        """Use the same 20–100 Hz gate as the cover shockwave."""
        return max(0.0, min(1.0, (bass_energy - 0.06) / 0.34))

    @staticmethod
    def _normalise_text(text: str) -> str:
        """Convert lyric punctuation and accents to the vector alphabet safely."""
        replacements = str.maketrans({"’": "'", "‘": "'", "–": "-", "—": "-"})
        normalised = unicodedata.normalize("NFKD", text.translate(replacements))
        return normalised.encode("ascii", "ignore").decode("ascii").upper()

    @staticmethod
    def _vector_width(text: str, size: int) -> float:
        """Return the width of the fixed-advance vector alphabet."""
        return max(0, len(text) - 1) * size * 0.78 + size * 0.68

    @classmethod
    def _draw_vector_line(
        cls,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: float,
        y: float,
        size: int,
    ) -> None:
        """Rasterize thin line glyphs, preserving the oscilloscope-vector look."""
        advance = size * 0.78
        width = max(3, round(size / 28))
        for character in text:
            if character == " ":
                x += advance
                continue
            glyph = cls._GLYPHS.get(character)
            if glyph is None:
                x += advance
                continue
            for start_x, start_y, end_x, end_y in glyph:
                draw.line(
                    (
                        (x + start_x * size * 0.68, y + start_y * size),
                        (x + end_x * size * 0.68, y + end_y * size),
                    ),
                    fill=255,
                    width=width,
                )
            x += advance
