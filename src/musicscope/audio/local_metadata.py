"""Metadata and artwork discovery for audio files stored on this computer."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen import MutagenError

from musicscope.artwork.cache import ArtworkCache
from musicscope.recognition.models import RecognizedTrack


@dataclass(frozen=True, slots=True)
class LocalTrackInfo:
    """Track data read from a local file and its containing album folder."""

    path: Path
    track: RecognizedTrack
    artwork_path: Path | None = None


class LocalMetadataReader:
    """Read common audio tags while gracefully supporting untagged files."""

    _FOLDER_COVER_NAMES = (
        "cover.jpg",
        "cover.jpeg",
        "cover.png",
        "folder.jpg",
        "folder.jpeg",
        "folder.png",
        "front.jpg",
        "front.jpeg",
        "front.png",
    )
    _TRACK_PREFIX = re.compile(r"^\s*(\d{1,3})\s*[-._]\s*")

    def __init__(self, cache: ArtworkCache | None = None) -> None:
        self._cache = cache or ArtworkCache.default()

    def read(self, path: Path) -> LocalTrackInfo:
        """Return tags, album-folder fallback and an embedded/folder cover when available."""
        tags = self._read_tags(path)
        title = self._without_track_prefix(self._tag(tags, "title") or self._filename_title(path))
        artist = self._tag(tags, "artist") or self._filename_artist(path) or "Local file"
        album = self._tag(tags, "album") or path.parent.name
        track_number = self._track_number(self._tag(tags, "tracknumber"))
        track_number = track_number or self._filename_number(path)
        track = RecognizedTrack(title, artist, album=album, track_number=track_number)
        artwork_path = self._folder_artwork(path.parent) or self._embedded_artwork(path)
        return LocalTrackInfo(path=path, track=track, artwork_path=artwork_path)

    @staticmethod
    def _read_tags(path: Path) -> Any:
        try:
            audio = MutagenFile(path, easy=True)
        except (MutagenError, OSError, ValueError):
            return None
        return audio.tags if audio is not None else None

    @staticmethod
    def _tag(tags: Any, name: str) -> str | None:
        if tags is None:
            return None
        try:
            value = tags.get(name)
        except AttributeError:
            return None
        if isinstance(value, (list, tuple)):
            value = value[0] if value else None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    @staticmethod
    def _track_number(value: str | None) -> int | None:
        if value is None:
            return None
        number = value.partition("/")[0].strip()
        return int(number) if number.isdigit() and int(number) > 0 else None

    @staticmethod
    def _filename_title(path: Path) -> str:
        stem = LocalMetadataReader._without_track_prefix(path.stem)
        _artist, separator, title = stem.partition(" - ")
        return LocalMetadataReader._without_track_prefix(title) if separator and title else stem

    @staticmethod
    def _filename_artist(path: Path) -> str | None:
        stem = LocalMetadataReader._without_track_prefix(path.stem)
        artist, separator, _title = stem.partition(" - ")
        return artist if separator and artist else None

    @classmethod
    def _filename_number(cls, path: Path) -> int | None:
        match = cls._TRACK_PREFIX.match(path.stem)
        return int(match.group(1)) if match is not None else None

    @classmethod
    def _without_track_prefix(cls, value: str) -> str:
        """Remove filename-only track labels before metadata and lyric searches."""
        return cls._TRACK_PREFIX.sub("", value, count=1).strip()

    def _folder_artwork(self, directory: Path) -> Path | None:
        try:
            images = [
                candidate
                for candidate in directory.iterdir()
                if candidate.is_file()
                and candidate.suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
        except OSError:
            return None
        candidates = {candidate.name.casefold(): candidate for candidate in images}
        named_cover = next(
            (candidates[name] for name in self._FOLDER_COVER_NAMES if name in candidates),
            None,
        )
        if named_cover is not None:
            return named_cover
        return next(
            (candidate for candidate in sorted(images) if "cover" in candidate.stem.casefold()),
            None,
        )

    def _embedded_artwork(self, path: Path) -> Path | None:
        try:
            audio = MutagenFile(path)
        except (MutagenError, OSError, ValueError):
            return None
        if audio is None:
            return None
        image = self._embedded_image(audio)
        if image is None:
            return None
        content, suffix = image
        source = f"local-file://{path.resolve()}#embedded-artwork"
        try:
            cached = self._cache.load(source, suffix)
            return cached or self._cache.store(source, content, suffix)
        except OSError:
            return None

    @staticmethod
    def _embedded_image(audio: Any) -> tuple[bytes, str] | None:
        pictures = getattr(audio, "pictures", ())
        for picture in pictures:
            data = getattr(picture, "data", None)
            if isinstance(data, bytes):
                return data, LocalMetadataReader._suffix(getattr(picture, "mime", None))

        tags = getattr(audio, "tags", None)
        getall = getattr(tags, "getall", None)
        if callable(getall):
            for picture in getall("APIC"):
                data = getattr(picture, "data", None)
                if isinstance(data, bytes):
                    return data, LocalMetadataReader._suffix(getattr(picture, "mime", None))
        if tags is not None:
            try:
                covers = tags.get("covr", ())
            except AttributeError:
                covers = ()
            for cover in covers:
                if isinstance(cover, bytes):
                    return cover, ".png" if cover.startswith(b"\x89PNG") else ".jpg"
        return None

    @staticmethod
    def _suffix(mime: object) -> str:
        return ".png" if mime == "image/png" else ".jpg"
