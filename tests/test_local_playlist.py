"""Tests for local dropped-file playlist management."""

from pathlib import Path

from musicscope.artwork.cache import ArtworkCache
from musicscope.audio.local_metadata import LocalMetadataReader, LocalTrackInfo
from musicscope.audio.local_playlist import LocalPlaylist
from musicscope.recognition.models import RecognizedTrack


def test_playlist_adds_supported_files_and_extracts_filename_metadata(tmp_path: Path) -> None:
    track = tmp_path / "Daft Punk - One More Time.mp3"
    ignored = tmp_path / "notes.txt"
    track.touch()
    ignored.touch()
    playlist = LocalPlaylist()

    added = playlist.add((tmp_path,))

    assert added == (track.resolve(),)
    local_track = playlist.track_at(1)
    assert local_track is not None
    assert local_track.title == "One More Time"
    assert local_track.artist == "Daft Punk"


def test_playlist_deduplicates_dropped_files(tmp_path: Path) -> None:
    track = tmp_path / "song.flac"
    track.touch()
    playlist = LocalPlaylist()

    playlist.add((track,))

    assert playlist.add((track,)) == ()
    local_track = playlist.track_at(1)
    assert local_track is not None
    assert local_track.artist == "Local file"


def test_playlist_deduplicates_equivalent_metadata_and_ignores_cover_named_audio(
    tmp_path: Path,
) -> None:
    first_copy = tmp_path / "Artist - Song.mp3"
    second_copy = tmp_path / "Artist - Song.flac"
    artwork = tmp_path / "cover.mp3"
    for file in (first_copy, second_copy, artwork):
        file.touch()
    playlist = LocalPlaylist()

    added = playlist.add((tmp_path,))

    assert added == (second_copy.resolve(),)
    assert playlist.size == 1


def test_playlist_ignores_macos_resource_fork_audio_files(tmp_path: Path) -> None:
    track = tmp_path / "Artist - Song.mp3"
    resource_fork = tmp_path / "._Artist - Song.mp3"
    track.touch()
    resource_fork.touch()
    playlist = LocalPlaylist()

    playlist.add((tmp_path,))

    assert playlist.paths == (track.resolve(),)


def test_metadata_reader_removes_filename_track_prefix_for_lyrics_lookup(tmp_path: Path) -> None:
    track = tmp_path / "02 - Daft Punk - Around the World.mp3"
    track.touch()

    item = LocalMetadataReader().read(track)

    assert item.track.title == "Around the World"
    assert item.track.artist == "Daft Punk"
    assert item.track.track_number == 2


def test_metadata_reader_removes_track_prefix_from_embedded_title(
    monkeypatch,
    tmp_path: Path,
) -> None:
    track = tmp_path / "file.mp3"
    track.touch()

    class TaggedAudio:
        tags = {"title": ["03 - Song"], "artist": ["Artist"]}

    def read_tags(*_args: object, **_kwargs: object) -> TaggedAudio:
        return TaggedAudio()

    monkeypatch.setattr("musicscope.audio.local_metadata.MutagenFile", read_tags)

    assert LocalMetadataReader().read(track).track.title == "Song"


def test_playlist_can_move_remove_and_clear_tracks(tmp_path: Path) -> None:
    first = tmp_path / "A - First.mp3"
    second = tmp_path / "B - Second.mp3"
    third = tmp_path / "C - Third.mp3"
    for track in (first, second, third):
        track.touch()
    playlist = LocalPlaylist()
    playlist.add((first, second, third))

    assert playlist.move(3, 1)
    assert playlist.track_at(1).title == "Third"  # type: ignore[union-attr]
    assert playlist.remove(2) is not None
    assert playlist.size == 2
    playlist.clear()

    assert playlist.size == 0


def test_folder_playlist_orders_tracks_by_embedded_track_number(tmp_path: Path) -> None:
    album = tmp_path / "Album"
    album.mkdir()
    later = album / "z.mp3"
    first = album / "a.mp3"
    later.touch()
    first.touch()

    class FakeReader:
        def read(self, path: Path) -> LocalTrackInfo:
            number = 1 if path == first else 2
            return LocalTrackInfo(path, RecognizedTrack(path.stem, "Artist", track_number=number))

    playlist = LocalPlaylist(metadata_reader=FakeReader())
    playlist.add((album,))

    assert playlist.paths == (first.resolve(), later.resolve())


def test_metadata_reader_uses_tags_and_folder_cover(monkeypatch, tmp_path: Path) -> None:
    track = tmp_path / "01 - Untagged.mp3"
    cover = tmp_path / "cover.png"
    track.touch()
    cover.touch()

    class TaggedAudio:
        tags = {
            "title": ["Tagged song"],
            "artist": ["Tagged artist"],
            "album": ["Tagged album"],
            "tracknumber": ["03/12"],
        }

    def read_tags(*_args: object, **_kwargs: object) -> TaggedAudio:
        return TaggedAudio()

    monkeypatch.setattr("musicscope.audio.local_metadata.MutagenFile", read_tags)

    item = LocalMetadataReader().read(track)

    assert item.track.title == "Tagged song"
    assert item.track.artist == "Tagged artist"
    assert item.track.album == "Tagged album"
    assert item.track.track_number == 3
    assert item.artwork_path == cover


def test_metadata_reader_uses_folder_name_and_embedded_cover(monkeypatch, tmp_path: Path) -> None:
    album = tmp_path / "Album folder"
    album.mkdir()
    track = album / "Artist - Song.flac"
    track.touch()

    class Picture:
        data = b"embedded-cover"
        mime = "image/jpeg"

    class TaggedAudio:
        tags = {}
        pictures = (Picture(),)

    def read_tags(*_args: object, **_kwargs: object) -> TaggedAudio:
        return TaggedAudio()

    monkeypatch.setattr("musicscope.audio.local_metadata.MutagenFile", read_tags)
    reader = LocalMetadataReader(ArtworkCache(tmp_path / "cache"))

    item = reader.read(track)

    assert item.track.album == "Album folder"
    assert item.artwork_path is not None
    assert item.artwork_path.read_bytes() == b"embedded-cover"
