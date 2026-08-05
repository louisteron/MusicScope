"""Timed lyric lookup and parsing, independent from playback and rendering."""

from musicscope.lyrics.lrclib import LrclibLyricsSource
from musicscope.lyrics.lyrics_ovh import LyricsOvhSource
from musicscope.lyrics.service import LyricsService
from musicscope.lyrics.source import FallbackLyricsSource, LyricsSource
from musicscope.lyrics.timing import LyricDisplay, display_at

__all__ = [
    "FallbackLyricsSource",
    "LrclibLyricsSource",
    "LyricsOvhSource",
    "LyricsService",
    "LyricsSource",
    "LyricDisplay",
    "display_at",
]
