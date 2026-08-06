"""ModernGL context creation."""

import moderngl


def create_context() -> moderngl.Context:
    """Wrap the GLFW-current OpenGL context with ModernGL and antialiasing."""
    # GLFW configures the multisampled default framebuffer before this context
    # is created; ModernGL does not require a separate multisample flag here.
    return moderngl.create_context()
