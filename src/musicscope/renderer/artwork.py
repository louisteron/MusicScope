"""OpenGL artwork renderer driven solely by scene state."""

from pathlib import Path

import moderngl
import numpy as np
from PIL import Image

from musicscope.scene.model import VisualState


class ArtworkRenderer:
    """Render a foreground artwork mark with an audio-reactive mesh distortion."""

    _LOGO_FILENAMES = {
        "frog": "frog.jpg",
        "jvb": "logo-jvb.png",
        "ram": "logo-ram.png",
        "cd": "disc-cd.png",
        "vinyl": "disc-vinyl.png",
    }

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        in vec2 in_uv;
        uniform float u_energy;
        uniform float u_time;
        out vec2 uv;
        void main() {
            float warp = sin(in_uv.y * 28.0 + u_time * 6.0) * (0.006 + u_energy * 0.028);
            float jitter = cos(in_uv.x * 22.0 - u_time * 4.0) * u_energy * 0.016;
            vec2 center = vec2(0.0, 0.22);
            float pulse = 1.0 + u_energy * 0.12 + sin(u_time * 8.0) * u_energy * 0.04;
            vec2 pulsed_position = center + (in_position - center) * pulse;
            uv = in_uv;
            gl_Position = vec4(pulsed_position.x + warp, pulsed_position.y + jitter, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        uniform sampler2D u_artwork;
        in vec2 uv;
        out vec4 fragment_color;
        void main() {
            vec4 source = texture(u_artwork, uv);
            if (source.a < 0.05) discard;
            float luminance = dot(source.rgb, vec3(0.2126, 0.7152, 0.0722));
            float phosphor_strength = 0.78 + luminance * 0.22;
            vec3 phosphor = vec3(0.10, 1.0, 0.34) * phosphor_strength;
            fragment_color = vec4(phosphor, source.a * 0.96);
        }
    """

    def __init__(
        self,
        context: moderngl.Context,
        logo: str = "frog",
        subdivisions: int = 24,
    ) -> None:
        self._context = context
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

    def select_logo(self, logo: str) -> None:
        """Select a bundled visual to load during the next render pass."""
        self._logo_path = self._assets_directory / self._LOGO_FILENAMES[logo]

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
        self._program["u_energy"].value = state.energy
        self._program["u_time"].value = elapsed
        self._vertex_array.render(mode=moderngl.TRIANGLES, vertices=self._vertex_count)
        self._context.disable(moderngl.BLEND)

    def _load_texture(self, artwork_path: Path) -> None:
        with Image.open(artwork_path) as image:
            # The frog is a photograph requiring background removal. The PNG
            # marks already contain their intended alpha channel.
            rgba = self._prepare_image(
                image,
                isolate_foreground=artwork_path.name == "frog.jpg",
                crop_transparent_border=artwork_path.name == "logo-jvb.png",
            )
            rgba = rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            texture = self._context.texture(rgba.size, components=4, data=rgba.tobytes())
        texture.build_mipmaps()
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        if self._texture is not None:
            self._texture.release()
        self._texture = texture
        self._loaded_path = str(artwork_path)

    @staticmethod
    def _prepare_image(
        image: Image.Image,
        isolate_foreground: bool,
        crop_transparent_border: bool = False,
    ) -> Image.Image:
        rgb = image.convert("RGB")
        if not isolate_foreground:
            artwork = image.convert("RGBA")
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
