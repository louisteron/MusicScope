"""Create a portable ZIP archive for one platform-specific MusicScope build."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    """Archive the source directory or macOS application bundle supplied by CI."""
    source = Path(sys.argv[1]).resolve()
    destination = Path(sys.argv[2]).resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(
        str(destination.with_suffix("")),
        "zip",
        root_dir=source.parent,
        base_dir=source.name,
    )


if __name__ == "__main__":
    main()
