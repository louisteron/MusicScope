"""Timed lyric lookup and parsing, independent from playback and rendering."""

from musicscope.lyrics.lrclib import LrclibLyricsSource
from musicscope.lyrics.musixmatch import MusixmatchLyricsSource
from musicscope.lyrics.service import LyricsService
from musicscope.lyrics.source import FallbackLyricsSource, TimedLyricsSource
from musicscope.lyrics.timing import LyricDisplay, display_at

__all__ = [
    "FallbackLyricsSource",
    "LrclibLyricsSource",
    "LyricsService",
    "LyricDisplay",
    "MusixmatchLyricsSource",
    "TimedLyricsSource",
    "display_at",
]
