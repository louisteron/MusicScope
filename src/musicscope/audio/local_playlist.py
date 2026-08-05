"""Local audio-file playlist management independent from playback."""

from pathlib import Path

from musicscope.audio.local_metadata import LocalMetadataReader, LocalTrackInfo
from musicscope.recognition.models import RecognizedTrack


class LocalPlaylist:
    """Own supported local audio paths and their display metadata."""

    _EXTENSIONS = {".aac", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
    _COVER_FILENAMES = {"albumart", "artwork", "cover", "folder", "front"}

    def __init__(self, metadata_reader: LocalMetadataReader | None = None) -> None:
        self._items: list[LocalTrackInfo] = []
        self._metadata_reader = metadata_reader or LocalMetadataReader()

    @property
    def paths(self) -> tuple[Path, ...]:
        """Return playlist paths in playback order."""
        return tuple(item.path for item in self._items)

    @property
    def size(self) -> int:
        """Return the number of tracks currently in the playlist."""
        return len(self._items)

    def add(self, dropped_paths: tuple[Path, ...]) -> tuple[Path, ...]:
        """Append audio files from dropped files or folders, without duplicates."""
        self._remove_duplicate_items()
        existing = {item.path.resolve() for item in self._items}
        track_keys = {self._track_key(item) for item in self._items}
        added_items: list[LocalTrackInfo] = []
        for path in dropped_paths:
            candidates = sorted(path.rglob("*")) if path.is_dir() else (path,)
            items_from_drop: list[LocalTrackInfo] = []
            for candidate in candidates:
                if not self._is_playlist_audio_file(candidate):
                    continue
                resolved = candidate.resolve()
                if resolved not in existing:
                    item = self._metadata_reader.read(resolved)
                    track_key = self._track_key(item)
                    if track_key in track_keys:
                        continue
                    existing.add(resolved)
                    track_keys.add(track_key)
                    items_from_drop.append(item)
            if path.is_dir():
                items_from_drop.sort(key=self._album_order)
            added_items.extend(items_from_drop)
        self._items.extend(added_items)
        return tuple(item.path for item in added_items)

    def track_at(self, one_based_index: int) -> RecognizedTrack | None:
        """Return simple filename-derived metadata for a player playlist index."""
        item = self.item_at(one_based_index)
        return item.track if item is not None else None

    def item_at(self, one_based_index: int) -> LocalTrackInfo | None:
        """Return the local metadata and cover associated with a playlist index."""
        if one_based_index < 1 or one_based_index > len(self._items):
            return None
        item = self._items[one_based_index - 1]
        return LocalTrackInfo(
            path=item.path,
            track=RecognizedTrack(
                item.track.title,
                item.track.artist,
                album=item.track.album,
                track_number=one_based_index,
            ),
            artwork_path=item.artwork_path,
        )

    def move(self, one_based_source: int, one_based_destination: int) -> bool:
        """Move one item to another playlist position."""
        if not (1 <= one_based_source <= len(self._items)):
            return False
        destination = max(1, min(one_based_destination, len(self._items)))
        item = self._items.pop(one_based_source - 1)
        self._items.insert(destination - 1, item)
        return True

    def remove(self, one_based_index: int) -> LocalTrackInfo | None:
        """Remove and return an individual local track."""
        if not (1 <= one_based_index <= len(self._items)):
            return None
        return self._items.pop(one_based_index - 1)

    def clear(self) -> None:
        """Remove every local track from the playlist."""
        self._items.clear()

    def index_of_path(self, path: Path) -> int | None:
        """Return a path's current one-based position after reordering."""
        resolved = path.resolve()
        return next(
            (index for index, item in enumerate(self._items, start=1) if item.path == resolved),
            None,
        )

    @staticmethod
    def _album_order(item: LocalTrackInfo) -> tuple[int, str]:
        """Use embedded track numbers before filenames for an album folder."""
        return (item.track.track_number or 1_000_000, item.path.name.casefold())

    @classmethod
    def _is_playlist_audio_file(cls, path: Path) -> bool:
        """Exclude album-art files even when they have a misleading audio suffix."""
        return (
            path.is_file()
            and not path.name.startswith("._")
            and not path.name.startswith(".")
            and path.suffix.casefold() in cls._EXTENSIONS
            and path.stem.casefold() not in cls._COVER_FILENAMES
        )

    def _remove_duplicate_items(self) -> None:
        """Clean duplicates left by previous drops before extending the playlist."""
        seen_paths: set[Path] = set()
        seen_tracks: set[tuple[str, str, str, int | None]] = set()
        unique_items: list[LocalTrackInfo] = []
        for item in self._items:
            resolved = item.path.resolve()
            track_key = self._track_key(item)
            if resolved in seen_paths or track_key in seen_tracks:
                continue
            seen_paths.add(resolved)
            seen_tracks.add(track_key)
            unique_items.append(item)
        self._items = unique_items

    @staticmethod
    def _track_key(item: LocalTrackInfo) -> tuple[str, str, str, int | None]:
        track = item.track
        return (
            track.artist.casefold().strip(),
            track.title.casefold().strip(),
            (track.album or "").casefold().strip(),
            track.track_number,
        )
