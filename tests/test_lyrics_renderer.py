"""Tests for lyric-line layout independent of OpenGL rendering."""

from PIL import Image, ImageDraw

from musicscope.renderer.lyrics import LyricsRenderer


def test_vector_glyphs_contain_only_line_segments() -> None:
    """Every glyph segment must have exactly two two-dimensional endpoints."""
    assert all(len(segment) == 4 for glyph in LyricsRenderer._GLYPHS.values() for segment in glyph)


def test_lyrics_wrap_preserves_every_word() -> None:
    """A long lyric must wrap rather than losing its final words."""
    draw = ImageDraw.Draw(Image.new("L", (1024, 420)))
    font = LyricsRenderer._font(42)
    lyric = "WHEN THE NIGHT IS LONG THE OSCILLOSCOPE KEEPS EVERY LAST WORD VISIBLE"

    lines = LyricsRenderer._wrap(draw, lyric, font, maximum_width=300)

    assert "".join(lines).replace(" ", "") == lyric.replace(" ", "")
    assert len(lines) > 1


def test_vector_wrap_never_splits_an_unbroken_word() -> None:
    """A long word remains whole while layout selects a smaller glyph size."""
    lyric = "SUPERCALIFRAGILISTICEXPIALIDOCIOUS"

    lines = LyricsRenderer._wrap_vector(lyric, size=42, maximum_width=120)

    assert lines == (lyric,)


def test_vector_layout_uses_the_vector_glyph_width() -> None:
    """The wider vector alphabet must wrap before the texture edge."""
    lyric = "UNITED IN GRIEF UNITED IN GRIEF"

    lines = LyricsRenderer._wrap_vector(lyric, size=100, maximum_width=900)

    assert len(lines) > 1
    assert all(LyricsRenderer._vector_width(line, 100) <= 900 for line in lines)


def test_layout_keeps_three_lines_inside_the_visible_texture_height() -> None:
    """The top and bottom of a long lyric must not be clipped."""
    draw = ImageDraw.Draw(Image.new("L", (1024, 420)))
    text = "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE"

    lines, font = LyricsRenderer._layout(LyricsRenderer.__new__(LyricsRenderer), draw, text)
    size = getattr(font, "size", 32)
    block_height = round(size * 1.10) * len(lines) + max(6, size // 9) * (len(lines) - 1)

    assert len(lines) <= 3
    assert block_height <= 360


def test_lyrics_text_normalisation_removes_accents_without_question_marks() -> None:
    """Unsupported Unicode must not turn into visible fallback question marks."""
    lyric = "J’ETAIS DÉJÀ LÀ — ÇA VA"

    assert LyricsRenderer._normalise_text(lyric) == "J'ETAIS DEJA LA - CA VA"
