"""Tests for keyboard-driven centre visual selection."""

import pytest

from musicscope.core.logo_selector import LogoSelector


def test_selector_wraps_forward_and_backward() -> None:
    selector = LogoSelector(("frog", "jvb", "ram"), "jvb")

    assert selector.advance() == "ram"
    assert selector.advance() == "frog"
    assert selector.advance(-1) == "ram"


def test_selector_rejects_an_unknown_initial_visual() -> None:
    with pytest.raises(ValueError, match="Current visual"):
        LogoSelector(("frog",), "vinyl")
