"""Timing rules for lyric disappearance and oscilloscope fallback."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LyricDisplay:
    """A lyric line and its current phosphor opacity."""

    line: str | None
    opacity: float = 0.0
    morph: float = 1.0


def display_at(
    lines: tuple[tuple[float, str], ...],
    playback_seconds: float,
    hold_seconds: float = 4.0,
    fade_seconds: float = 1.0,
    morph_seconds: float = 0.55,
    entry_effect: str = "FADE",
) -> LyricDisplay:
    """Fade only into confirmed long silences, never between nearby lyric lines."""
    active_index = next(
        (index for index in range(len(lines) - 1, -1, -1) if lines[index][0] <= playback_seconds),
        None,
    )
    if active_index is None:
        return LyricDisplay(None)
    timestamp, text = lines[active_index]
    age = playback_seconds - timestamp
    entry_progress = min(1.0, age / morph_seconds)
    if entry_effect == "NO FADE":
        return LyricDisplay(text, 1.0, 1.0)
    next_timestamp = lines[active_index + 1][0] if active_index + 1 < len(lines) else None
    long_silence = (
        next_timestamp is None or next_timestamp - timestamp > hold_seconds + fade_seconds
    )
    if not long_silence or age <= hold_seconds:
        if entry_effect == "MORPH":
            return LyricDisplay(text, 1.0, entry_progress)
        return LyricDisplay(text, entry_progress, 1.0)
    if age >= hold_seconds + fade_seconds:
        return LyricDisplay(None)
    return LyricDisplay(text, 1.0 - (age - hold_seconds) / fade_seconds, 1.0)
