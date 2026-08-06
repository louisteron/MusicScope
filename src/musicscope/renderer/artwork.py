"""OpenGL artwork renderer driven solely by scene state."""

from pathlib import Path

import moderngl
import numpy as np
from PIL import Image, ImageOps

from musicscope.renderer.color_settings import ColorMode, ColorSettings
from musicscope.renderer.track_info_settings import TrackInfoSettings
from musicscope.scene.model import VisualState


class ArtworkRenderer:
    """Render a fixed foreground artwork mark with a phosphor edge treatment."""

    _LOGO_FILENAMES = {
        "musicscope": "musicscope-logo.png",
    }

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        in vec2 in_uv;
        uniform float u_aspect_ratio;
        uniform int u_background;
        out vec2 uv;
        void main() {
            uv = in_uv;
            vec2 position = in_position;
            if (u_background == 1) position = in_uv * 2.0 - 1.0;
            float horizontal = in_position.x / u_aspect_ratio;
            if (u_background == 1) horizontal = position.x;
            gl_Position = vec4(horizontal, position.y, 0.0, 1.0);
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
        uniform int u_background;
        uniform int u_logo;
        uniform float u_aspect_ratio;
        in vec2 uv;
        out vec4 fragment_color;

        float luminance(vec3 color) {
            return dot(color, vec3(0.2126, 0.7152, 0.0722));
        }

        void main() {
            vec2 artwork_uv = uv;
            if (u_background == 1) {
                if (u_aspect_ratio >= 1.0) {
                    artwork_uv.y = 0.5 + (uv.y - 0.5) / u_aspect_ratio;
                } else {
                    artwork_uv.x = 0.5 + (uv.x - 0.5) * u_aspect_ratio;
                }
            }
            vec2 from_center = uv - vec2(0.5);
            float distance = length(from_center);
            vec2 direction = normalize(from_center + vec2(0.0001));
            float shockwave = sin(distance * 76.0 - u_time * 16.0) * u_bass * 0.0035;
            vec2 bass_warp = direction * shockwave;
            vec2 sample_uv = clamp(artwork_uv + bass_warp, vec2(0.001), vec2(0.999));
            vec4 sampled = texture(u_artwork, sample_uv);
            vec3 sampled_color = sampled.rgb;
            float logo_fill = float(u_logo) * sampled.a
                * smoothstep(0.25, 0.72, luminance(sampled_color));
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
            float edge_strength = max(contrast_edge, alpha_edge);
            float edge_softness = max(fwidth(edge_strength) * 1.8, 0.007);
            float trace = smoothstep(0.035 - edge_softness, 0.19 + edge_softness, edge_strength);
            float aura = smoothstep(0.006 - edge_softness, 0.105 + edge_softness, edge_strength);
            if (u_background == 1) {
                if (trace < 0.02 && logo_fill < 0.01) discard;
                vec3 neon = u_theme_color;
                if (u_color_mode == 1) {
                    neon = mix(max(sampled_color, vec3(0.10)), vec3(1.0), 0.22);
                }
                fragment_color = vec4(neon * (0.15 + aura * 0.20 + trace * 0.42 + logo_fill * 0.14),
                    aura * 0.16 + trace * 0.54 + logo_fill * 0.26);
                return;
            }
            if (trace < 0.02 && logo_fill < 0.01) discard;
            vec3 phosphor = u_theme_color;
            if (u_color_mode == 1) {
                float brightness = max(luminance(sampled_color), 0.25);
                phosphor = mix(max(sampled_color, vec3(0.10)), vec3(1.0), 0.22)
                    * (0.72 + brightness * 0.28);
            }
            phosphor *= 0.58 + aura * 0.18 + trace * 0.32 + logo_fill * 0.18;
            fragment_color = vec4(phosphor, aura * 0.20 + trace * 0.82 + logo_fill * 0.52);
        }
    """

    def __init__(
        self,
        context: moderngl.Context,
        logo: str = "musicscope",
        subdivisions: int = 24,
        color_settings: ColorSettings | None = None,
        track_info_settings: TrackInfoSettings | None = None,
    ) -> None:
        self._context = context
        self._color_settings = color_settings or ColorSettings()
        self._track_info_settings = track_info_settings or TrackInfoSettings()
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
        # Keep a neon background visible while metadata/artwork is still being
        # fetched; the bundled mark is replaced on the next rendered frame
        # after the real cover reaches the scene.
        self._program["u_background"].value = int(self._track_info_settings.lyrics_wave)
        self._program["u_logo"].value = int(artwork_path == self._logo_path)
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
            # Legacy raster marks can require isolation. The MusicScope logo
            # already contains transparency and is cropped to its visible art.
            rgba = self._prepare_image(
                image,
                isolate_foreground=artwork_path.name == "frog.jpg",
                crop_transparent_border=artwork_path == self._logo_path,
                crop_to_square=artwork_path != self._logo_path,
                output_size=2048 if artwork_path == self._logo_path else 512,
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
        output_size: int = 512,
    ) -> Image.Image:
        rgb = image.convert("RGB")
        if not isolate_foreground:
            artwork = image.convert("RGBA")
            if crop_to_square:
                return ImageOps.fit(
                    artwork,
                    (output_size, output_size),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            if crop_transparent_border:
                bounds = artwork.getchannel("A").getbbox()
                if bounds is not None:
                    artwork = artwork.crop(bounds)
            return ArtworkRenderer._fit_in_square(artwork, size=output_size)
        pixels = np.asarray(rgb)
        red, green, blue = (pixels[:, :, index] for index in range(3))
        mask = (red > 130) & (blue > 110) & (red - green > 25) & (blue - green > 12)
        alpha = Image.fromarray(np.where(mask, 255, 0).astype("uint8"))
        foreground = rgb.convert("RGBA")
        foreground.putalpha(alpha)
        bounds = alpha.getbbox()
        if bounds is not None:
            foreground = foreground.crop(bounds)
        return ArtworkRenderer._fit_in_square(foreground, size=output_size)

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
