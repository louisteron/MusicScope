"""Tests for errors reported by the optional physical-CD adapter."""

import builtins
import os

import pytest

from musicscope.recognition.cd import CdMetadataUnavailable, LibDiscIdReader


def test_reader_explains_when_libdiscid_cannot_be_loaded(monkeypatch) -> None:
    original_import = builtins.__import__

    def fail_discid_import(name, *args, **kwargs):
        if name == "discid":
            raise OSError("library not loaded")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_discid_import)

    with pytest.raises(CdMetadataUnavailable, match="could not be loaded"):
        LibDiscIdReader().read_id(None)


def test_reader_adds_a_homebrew_library_path_on_macos(monkeypatch) -> None:
    monkeypatch.setattr("musicscope.recognition.cd.sys.platform", "darwin")
    monkeypatch.setattr("musicscope.recognition.cd.os.path.isdir", lambda path: "opt" in path)
    monkeypatch.delenv("DYLD_FALLBACK_LIBRARY_PATH", raising=False)

    LibDiscIdReader._configure_macos_library_path()

    assert os.environ["DYLD_FALLBACK_LIBRARY_PATH"].endswith("libdiscid/lib")
