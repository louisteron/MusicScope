"""CRT phosphor grid rendered as a fullscreen ModernGL pass."""

from array import array

import moderngl

from musicscope.renderer.color_settings import ColorSettings


class CrtRenderer:
    """Draw a scan-lined oscilloscope background with a subtle grid."""

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        out vec2 position;
        void main() {
            position = in_position;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        in vec2 position;
        uniform float u_energy;
        uniform float u_time;
        uniform vec3 u_theme_color;
        uniform bool u_overlay;
        out vec4 fragment_color;

        float grid_line(float coordinate, float width) {
            float distance_to_line = abs(fract(coordinate) - 0.5);
            return smoothstep(0.5 - width, 0.5, distance_to_line);
        }

        void main() {
            vec2 curved = position * (1.0 + 0.045 * dot(position, position));
            vec2 scope_uv = curved * 0.5 + 0.5;
            vec2 divisions = vec2(12.0, 8.0);
            vec2 grid_position = scope_uv * divisions;

            float vertical = grid_line(grid_position.x, 0.030);
            float horizontal = grid_line(grid_position.y, 0.030);
            float vertical_dots = step(0.52, fract(grid_position.y * 5.0));
            float horizontal_dots = step(0.52, fract(grid_position.x * 5.0));
            float dotted_grid = max(vertical * vertical_dots, horizontal * horizontal_dots);

            float vertical_axis = 1.0 - smoothstep(0.0, 0.004, abs(curved.x));
            float horizontal_axis = 1.0 - smoothstep(0.0, 0.004, abs(curved.y));
            float vertical_ticks = step(0.36, fract(scope_uv.y * 72.0));
            float horizontal_ticks = step(0.36, fract(scope_uv.x * 72.0));
            float axis = max(vertical_axis * vertical_ticks, horizontal_axis * horizontal_ticks);

            float horizontal_edge = min(scope_uv.x, 1.0 - scope_uv.x);
            float vertical_edge = min(scope_uv.y, 1.0 - scope_uv.y);
            float edge_distance = min(horizontal_edge, vertical_edge);
            float border = 1.0 - smoothstep(0.002, 0.008, edge_distance);
            float grid_line_intensity = max(dotted_grid * 0.78, max(axis * 1.00, border * 1.00));
            float scan = 0.86 + 0.14 * sin(gl_FragCoord.y * 3.14159);
            float noiseSeed = dot(gl_FragCoord.xy + u_time, vec2(12.9898, 78.233));
            float noise = fract(sin(noiseSeed) * 43758.5453);
            float vignette = max(0.24, 1.0 - 0.48 * dot(position, position));
            vec3 base = vec3(0.0004, 0.006, 0.0018);
            vec3 phosphor = u_theme_color * 0.34 * (grid_line_intensity + u_energy * 0.06);
            vec3 crt = ((base + phosphor) * scan + noise * 0.003) * vignette;
            fragment_color = u_overlay ? vec4(phosphor * scan * vignette, 0.42) : vec4(crt, 1.0);
        }
    """

    def __init__(
        self,
        context: moderngl.Context,
        color_settings: ColorSettings | None = None,
    ) -> None:
        self._color_settings = color_settings or ColorSettings()
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        positions = array("f", (-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
        vertices = context.buffer(data=positions.tobytes())
        self._vertex_array = context.vertex_array(self._program, [(vertices, "2f", "in_position")])

    def render(self, energy: float, elapsed: float, overlay: bool = False) -> None:
        """Draw the background before all phosphor traces."""
        self._program["u_energy"].value = energy
        self._program["u_time"].value = elapsed
        self._program["u_theme_color"].value = self._color_settings.theme_color
        self._program["u_overlay"].value = overlay
        if overlay:
            self._context.enable(moderngl.BLEND)
            self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self._vertex_array.render(mode=moderngl.TRIANGLE_STRIP)
        if overlay:
            self._context.disable(moderngl.BLEND)
