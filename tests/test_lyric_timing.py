"""Tests for lyric fade-out and the delayed oscilloscope fallback."""

import pytest

from musicscope.lyrics.timing import display_at


def test_lyric_fades_only_during_the_final_second() -> None:
    display = display_at(((10.0, "HELLO"),), 14.5)

    assert display.line == "HELLO"
    assert display.opacity == pytest.approx(0.5)


def test_fade_entry_uses_a_short_fade_for_each_new_lyric() -> None:
    display = display_at(((10.0, "HELLO"),), 10.01)

    assert display.line == "HELLO"
    assert display.opacity == pytest.approx(0.01 / 0.55)
    assert display.morph == 1.0


def test_new_lyric_morphs_from_the_scope_trace_into_full_letters() -> None:
    display = display_at(((10.0, "HELLO"),), 10.275, entry_effect="MORPH")

    assert display.opacity == 1.0
    assert display.morph == pytest.approx(0.5)


def test_no_fade_entry_displays_a_new_lyric_immediately() -> None:
    display = display_at(((10.0, "HELLO"),), 30.0, entry_effect="NO FADE")

    assert display.line == "HELLO"
    assert display.opacity == 1.0
    assert display.morph == 1.0


def test_lyric_is_removed_after_five_seconds_without_a_new_line() -> None:
    display = display_at(((10.0, "HELLO"),), 15.0)

    assert display.line is None
    assert display.opacity == 0.0


def test_new_lyric_replaces_the_old_one_before_the_scope_fallback() -> None:
    display = display_at(((10.0, "HELLO"), (12.5, "WORLD")), 13.1)

    assert display.line == "WORLD"
    assert display.opacity == 1.0


def test_nearby_lyrics_do_not_trigger_a_scope_transition_between_lines() -> None:
    display = display_at(((10.0, "HELLO"), (14.5, "WORLD")), 14.25)

    assert display.line == "HELLO"
    assert display.opacity == 1.0
