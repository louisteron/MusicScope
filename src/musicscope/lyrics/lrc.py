"""Parser for standard timestamped LRC lyric documents."""

import re

_TIMESTAMP = re.compile(r"\[(?P<minutes>\d+):(?P<seconds>\d{2}(?:\.\d{1,3})?)\]")


def parse_lrc(content: str) -> tuple[tuple[float, str], ...]:
    """Parse timed LRC lines, ignoring metadata and empty lyric text."""
    lines: list[tuple[float, str]] = []
    for raw_line in content.splitlines():
        timestamps = tuple(_TIMESTAMP.finditer(raw_line))
        text = _TIMESTAMP.sub("", raw_line).strip()
        if not text:
            continue
        for timestamp in timestamps:
            seconds = int(timestamp["minutes"]) * 60 + float(timestamp["seconds"])
            lines.append((seconds, text))
    return tuple(sorted(lines))
