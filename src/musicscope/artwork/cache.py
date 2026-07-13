"""Content-addressed local storage for downloaded images."""

import hashlib
import os
from pathlib import Path


class ArtworkCache:
    """Persist image bytes atomically under a stable URL-derived filename."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    @classmethod
    def default(cls) -> "ArtworkCache":
        """Create the cache under the configured or conventional user cache directory."""
        directory = Path(os.getenv("MUSICSCOPE_CACHE_DIR", Path.home() / ".cache" / "musicscope"))
        return cls(directory / "artwork")

    def path_for(self, source_url: str, suffix: str = ".jpg") -> Path:
        """Return the cache location assigned to an artwork URL."""
        digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
        return self._directory / f"{digest}{suffix}"

    def load(self, source_url: str, suffix: str = ".jpg") -> Path | None:
        """Return an existing cached file, if any."""
        path = self.path_for(source_url, suffix)
        return path if path.is_file() else None

    def store(self, source_url: str, content: bytes, suffix: str = ".jpg") -> Path:
        """Atomically write artwork bytes and return the final file path."""
        path = self.path_for(source_url, suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
        return path
