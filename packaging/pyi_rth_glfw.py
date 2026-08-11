"""Configure the GLFW binary location before importing the glfw package."""

import os
import sys

if sys.platform.startswith("linux"):
    # The release archive ships the Linux GLFW runtime in this directory.
    # Use it explicitly rather than relying on libraries installed by users.
    os.environ.setdefault("PYGLFW_LIBRARY_VARIANT", "x11")
