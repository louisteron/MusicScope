"""Command line entry point for MusicScope."""

import os
import sys
from pathlib import Path


def _configure_frozen_glfw() -> None:
    """Point glfw at the library bundled next to a frozen application."""
    if not getattr(sys, "frozen", False) or os.environ.get("PYGLFW_LIBRARY"):
        return
    resource_directory = Path(sys.executable).resolve().parent.parent / "Resources" / "glfw"
    candidates = (
        "libglfw.3.dylib",
        "libglfw.so.3",
        "libglfw.so",
        "glfw3.dll",
    )
    library = next(
        (resource_directory / name for name in candidates if (resource_directory / name).is_file()),
        None,
    )
    if library is not None:
        os.environ["PYGLFW_LIBRARY"] = str(library)


_configure_frozen_glfw()

from musicscope.core.application import main  # noqa: E402

__all__ = ["main"]


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()
