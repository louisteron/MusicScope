"""Stateful selection of bundled centre visuals."""


class LogoSelector:
    """Cycle through a fixed, validated sequence of visual names."""

    def __init__(self, names: tuple[str, ...], current: str) -> None:
        if not names:
            raise ValueError("At least one visual name is required.")
        if current not in names:
            raise ValueError("Current visual must be part of the available names.")
        self._names = names
        self._index = names.index(current)

    @property
    def current(self) -> str:
        """Return the selected visual name."""
        return self._names[self._index]

    def advance(self, amount: int = 1) -> str:
        """Move selection forward or backward, wrapping at both ends."""
        self._index = (self._index + amount) % len(self._names)
        return self.current
