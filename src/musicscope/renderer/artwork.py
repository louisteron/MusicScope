"""OpenGL artwork renderer driven solely by scene state."""

from pathlib import Path

import moderngl
import numpy as np
from PIL import Image, ImageOps

from musicscope.renderer.color_settings import ColorMode, ColorSettings
from musicscope.scene.model import VisualState


class ArtworkRenderer:
    """Render a fixed foreground artwork mark with a phosphor edge treatment."""

    _LOGO_FILENAMES = {
        "frog": "frog.jpg",
    }

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
        uniform sampler2D u_artwork;
        uniform vec2 u_texel_size;
        uniform float u_bass;
        uniform float u_time;
        uniform vec3 u_theme_color;
        uniform int u_color_mode;
        in vec2 uv;
        out vec4 fragment_color;

        float luminance(vec3 color) {
            return dot(color, vec3(0.2126, 0.7152, 0.0722));
        }

        void main() {
            vec2 from_center = uv - vec2(0.5);
            float distance = length(from_center);
            vec2 direction = normalize(from_center + vec2(0.0001));
            float shockwave = sin(distance * 76.0 - u_time * 16.0) * u_bass * 0.0035;
            vec2 bass_warp = direction * shockwave;
            vec2 sample_uv = clamp(uv + bass_warp, vec2(0.001), vec2(0.999));
            vec2 x_offset = vec2(u_texel_size.x, 0.0);
            vec2 y_offset = vec2(0.0, u_texel_size.y);
            vec4 left = texture(u_artwork, sample_uv - x_offset);
            vec4 right = texture(u_artwork, sample_uv + x_offset);
            vec4 lower = texture(u_artwork, sample_uv - y_offset);
            vec4 upper = texture(u_artwork, sample_uv + y_offset);
            float horizontal_edge = abs(luminance(left.rgb) - luminance(right.rgb));
            float vertical_edge = abs(luminance(lower.rgb) - luminance(upper.rgb));
            float contrast_edge = max(horizontal_edge, vertical_edge);
            float alpha_edge = max(abs(left.a - right.a), abs(lower.a - upper.a));
            float trace = smoothstep(0.035, 0.19, max(contrast_edge, alpha_edge));
            if (trace < 0.02) discard;
            vec3 sampled_color = texture(u_artwork, sample_uv).rgb;
            vec3 phosphor = u_theme_color;
            if (u_color_mode == 1) {
                float brightness = max(luminance(sampled_color), 0.25);
                phosphor = mix(max(sampled_color, vec3(0.10)), vec3(1.0), 0.22)
                    * (0.72 + brightness * 0.28);
            }
            phosphor *= 0.72 + trace * 0.28;
            fragment_color = vec4(phosphor, trace * 0.94);
        }
    """

    def __init__(
        self,
        context: moderngl.Context,
        logo: str = "frog",
        subdivisions: int = 24,
        color_settings: ColorSettings | None = None,
    ) -> None:
        self._context = context
        self._color_settings = color_settings or ColorSettings()
        self._assets_directory = Path(__file__).resolve().parents[1] / "assets"
        self._logo_path = self._assets_directory / self._LOGO_FILENAMES[logo]
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        vertices = self._mesh(subdivisions)
        buffer = context.buffer(vertices.tobytes())
        self._vertex_array = context.vertex_array(
            self._program,
            [(buffer, "2f 2f", "in_position", "in_uv")],
        )
        self._vertex_count = len(vertices)
        self._texture: moderngl.Texture | None = None
        self._loaded_path: str | None = None
        self._load_texture(self._logo_path)

    def render(self, state: VisualState, elapsed: float) -> None:
        """Render the bundled logo, or future scene artwork when it is available."""
        artwork_path = Path(state.artwork_path) if state.artwork_path else self._logo_path
        if str(artwork_path) != self._loaded_path:
            self._load_texture(artwork_path)
        if self._texture is None:
            return
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self._texture.use(location=0)
        self._program["u_artwork"].value = 0
        self._program["u_aspect_ratio"].value = self._framebuffer_aspect_ratio()
        self._program["u_texel_size"].value = (
            1.0 / self._texture.width,
            1.0 / self._texture.height,
        )
        bass_energy = self._bass_motion(state.bass_energy) if state.artwork_path else 0.0
        self._program["u_bass"].value = bass_energy
        self._program["u_time"].value = elapsed
        self._program["u_theme_color"].value = self._color_settings.theme_color
        self._program["u_color_mode"].value = tuple(ColorMode).index(self._color_settings.mode)
        self._vertex_array.render(mode=moderngl.TRIANGLES, vertices=self._vertex_count)
        self._context.disable(moderngl.BLEND)

    def _framebuffer_aspect_ratio(self) -> float:
        """Return the physical display ratio used to keep the artwork square."""
        _, _, width, height = self._context.viewport
        return width / height if height else 1.0

    @staticmethod
    def _bass_motion(bass_energy: float) -> float:
        """Gate line motion to pronounced energy from the 20–100 Hz band."""
        return float(np.clip((bass_energy - 0.06) / 0.34, 0.0, 1.0))

    def _load_texture(self, artwork_path: Path) -> None:
        with Image.open(artwork_path) as image:
            # The frog is a photograph requiring background removal. The PNG
            # marks already contain their intended alpha channel.
            rgba = self._prepare_image(
                image,
                isolate_foreground=artwork_path.name == "frog.jpg",
                crop_to_square=artwork_path != self._logo_path,
            )
            if artwork_path != self._logo_path:
                self._color_settings.primary_color = self._dominant_color(rgba)
            rgba = rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            texture = self._context.texture(rgba.size, components=4, data=rgba.tobytes())
        texture.build_mipmaps()
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        if self._texture is not None:
            self._texture.release()
        self._texture = texture
        self._loaded_path = str(artwork_path)

    @staticmethod
    def _dominant_color(image: Image.Image) -> tuple[float, float, float]:
        """Extract a bright, saturated representative colour from cover artwork."""
        rgba = np.asarray(image.convert("RGBA"), dtype="f4")
        pixels = rgba[:, :, :3][rgba[:, :, 3] > 127] / 255.0
        if pixels.size == 0:
            return (0.10, 1.0, 0.34)
        saturation = pixels.max(axis=1) - pixels.min(axis=1)
        brightness = pixels.max(axis=1)
        candidates = pixels[(saturation > 0.16) & (brightness > 0.12)]
        color = candidates.mean(axis=0) if candidates.size else pixels.mean(axis=0)
        return tuple((color / max(float(color.max()), 0.20)).clip(0.18, 1.0))  # type: ignore[return-value]

    @staticmethod
    def _prepare_image(
        image: Image.Image,
        isolate_foreground: bool,
        crop_transparent_border: bool = False,
        crop_to_square: bool = False,
    ) -> Image.Image:
        rgb = image.convert("RGB")
        if not isolate_foreground:
            artwork = image.convert("RGBA")
            if crop_to_square:
                return ImageOps.fit(
                    artwork,
                    (512, 512),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            if crop_transparent_border:
                bounds = artwork.getchannel("A").getbbox()
                if bounds is not None:
                    artwork = artwork.crop(bounds)
            return ArtworkRenderer._fit_in_square(artwork)
        pixels = np.asarray(rgb)
        red, green, blue = (pixels[:, :, index] for index in range(3))
        mask = (red > 130) & (blue > 110) & (red - green > 25) & (blue - green > 12)
        alpha = Image.fromarray(np.where(mask, 255, 0).astype("uint8"))
        foreground = rgb.convert("RGBA")
        foreground.putalpha(alpha)
        bounds = alpha.getbbox()
        if bounds is not None:
            foreground = foreground.crop(bounds)
        return ArtworkRenderer._fit_in_square(foreground)

    @staticmethod
    def _fit_in_square(image: Image.Image, size: int = 512) -> Image.Image:
        """Fit an artwork in a transparent square without changing its aspect ratio."""
        width, height = image.size
        scale = min(size / width, size / height)
        fitted_size = (round(width * scale), round(height * scale))
        fitted = image.resize(fitted_size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size))
        offset = ((size - fitted.width) // 2, (size - fitted.height) // 2)
        canvas.alpha_composite(fitted, offset)
        return canvas

    def _mesh(self, subdivisions: int) -> np.ndarray:
        cells = []
        for row in range(subdivisions):
            for column in range(subdivisions):
                cells.extend(self._cell(column, row, subdivisions))
        return np.asarray(cells, dtype="f4")

    def _cell(self, column: int, row: int, subdivisions: int) -> tuple[tuple[float, ...], ...]:
        left = column / subdivisions
        right = (column + 1) / subdivisions
        bottom = row / subdivisions
        top = (row + 1) / subdivisions
        def vertex(x: float, y: float) -> tuple[float, ...]:
            return (x * 0.88 - 0.44, y * 0.88 - 0.22, x, y)
        return (
            vertex(left, bottom),
            vertex(right, bottom),
            vertex(right, top),
            vertex(left, bottom),
            vertex(right, top),
            vertex(left, top),
        )
