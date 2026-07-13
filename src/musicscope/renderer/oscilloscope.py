"""Phosphor traces for the waveform and central animated emblem."""

import math

import moderngl
import numpy as np

from musicscope.scene.model import VisualState


class OscilloscopeRenderer:
    """Render an audio trace and an emblem whose contours respond to sound."""

    _VERTEX_SHADER = """
        #version 330
        in vec2 in_position;
        uniform float u_intensity;
        uniform float u_opacity;
        out float intensity;
        out float opacity;
        void main() {
            intensity = u_intensity;
            opacity = u_opacity;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    """
    _FRAGMENT_SHADER = """
        #version 330
        in float intensity;
        in float opacity;
        out vec4 fragment_color;
        void main() {
            fragment_color = vec4(0.12 * intensity, intensity, 0.36 * intensity, opacity);
        }
    """

    def __init__(self, context: moderngl.Context, sample_count: int = 512) -> None:
        self._context = context
        self._sample_count = sample_count
        self._display_waveform: np.ndarray | None = None
        self._last_frame_time: float | None = None
        self._program = context.program(
            vertex_shader=self._VERTEX_SHADER,
            fragment_shader=self._FRAGMENT_SHADER,
        )
        self._buffer = context.buffer(reserve=sample_count * 6 * 2 * 4, dynamic=True)
        content = [(self._buffer, "2f", "in_position")]
        self._vertex_array = context.vertex_array(self._program, content)

    def render(self, state: VisualState, elapsed: float) -> None:
        """Draw a centered phosphor waveform with a multi-pass CRT glow."""
        waveform = self._waveform_vertices(self._interpolate_waveform(state.waveform, elapsed))
        intensity = state.energy * 1.2 + 0.35
        self._context.enable(moderngl.BLEND)
        self._context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self._draw(waveform, intensity=intensity, thickness=0.020, opacity=0.018)
        self._draw(waveform, intensity=intensity, thickness=0.0040, opacity=0.16)
        self._draw(waveform, intensity=intensity, thickness=0.030, opacity=0.06)
        self._draw(waveform, intensity=intensity, thickness=0.012, opacity=0.16)
        self._draw(waveform, intensity=intensity, thickness=0.0045, opacity=0.90)
        self._context.disable(moderngl.BLEND)

    def _draw(
        self,
        vertices: np.ndarray,
        intensity: float,
        thickness: float,
        opacity: float,
    ) -> None:
        self._program["u_intensity"].value = min(intensity, 1.0)
        self._program["u_opacity"].value = opacity
        stroke = self._stroke_vertices(vertices, thickness)
        self._buffer.write(stroke.tobytes())
        self._vertex_array.render(mode=moderngl.TRIANGLES, vertices=len(stroke))

    @staticmethod
    def _stroke_vertices(vertices: np.ndarray, thickness: float) -> np.ndarray:
        """Expand a polyline into triangles so thickness works on every OpenGL driver."""
        start = vertices[:-1]
        end = vertices[1:]
        direction = end - start
        length = np.linalg.norm(direction, axis=1, keepdims=True)
        normal = np.divide(
            np.column_stack((-direction[:, 1], direction[:, 0])),
            length,
            out=np.zeros_like(direction),
            where=length > 0.0,
        ) * thickness
        triangles = (
            start + normal,
            start - normal,
            end + normal,
            start - normal,
            end - normal,
            end + normal,
        )
        return np.stack(triangles, axis=1).reshape(-1, 2).astype("f4", copy=False)

    def _interpolate_waveform(self, waveform: tuple[float, ...], elapsed: float) -> np.ndarray:
        target = np.asarray(waveform or (0.0,) * self._sample_count, dtype="f4")
        target = np.resize(target, self._sample_count)
        if self._display_waveform is None:
            self._display_waveform = target
            self._last_frame_time = elapsed
            return target
        previous_time = self._last_frame_time if self._last_frame_time is not None else elapsed
        delta_time = max(0.0, elapsed - previous_time)
        blend = 1.0 - math.exp(-delta_time * 32.0)
        self._display_waveform += (target - self._display_waveform) * blend
        self._last_frame_time = elapsed
        return self._display_waveform

    def _waveform_vertices(self, waveform: tuple[float, ...] | np.ndarray) -> np.ndarray:
        values = np.asarray(waveform if len(waveform) else (0.0,) * self._sample_count, dtype="f4")
        values = np.resize(values, self._sample_count)
        values = self._trigger(values)
        values = np.convolve(values, np.full(5, 0.2, dtype="f4"), mode="same")
        x = np.linspace(-0.92, 0.92, self._sample_count, dtype="f4")
        y = values * 0.30
        return np.column_stack((x, y))

    def _trigger(self, values: np.ndarray) -> np.ndarray:
        rising_edges = np.flatnonzero((values[:-1] <= 0.0) & (values[1:] > 0.0))
        if rising_edges.size == 0:
            return values
        preferred_edge = rising_edges[np.argmin(np.abs(rising_edges - len(values) // 4))]
        return np.roll(values, -int(preferred_edge))

    def _sweep_vertices(self, elapsed: float) -> np.ndarray:
        position = -0.92 + (elapsed * 0.32 % 1.84)
        return np.asarray(((position, -0.90), (position, 0.90)), dtype="f4")

    def _emblem_vertices(self, energy: float, elapsed: float) -> np.ndarray:
        angles = np.linspace(0.0, math.tau, self._sample_count, dtype="f4")
        idle_pulse = 0.025 * math.sin(elapsed * 1.8)
        wobble = 0.035 + energy * 0.10
        radius = 0.38 + idle_pulse + wobble * np.sin(angles * 10.0 + elapsed * 7.0)
        x = radius * np.cos(angles * 3.0) * 0.90
        y = radius * np.sin(angles * 2.0) * 0.84 + 0.18
        return np.column_stack((x, y))
