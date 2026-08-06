"""Resolve the external mpv executable used for local playback."""

from __future__ import annotations

import sys
from pathlib import Path


def resolve_mpv_executable(
    *,
    platform: str = sys.platform,
    frozen: bool | None = None,
    executable: Path | None = None,
) -> str:
    """Prefer the mpv runtime packaged beside a frozen Windows application."""
    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    app_executable = Path(sys.executable) if executable is None else executable
    bundled_mpv = app_executable.resolve().parent / "mpv" / "mpv.exe"
    if platform == "win32" and is_frozen and bundled_mpv.is_file():
        return str(bundled_mpv)
    return "mpv"
