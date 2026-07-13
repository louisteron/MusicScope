"""ModernGL context creation."""

import moderngl


def create_context() -> moderngl.Context:
    """Wrap the GLFW-current OpenGL context with ModernGL."""
    return moderngl.create_context()
