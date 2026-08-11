from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class CurrentRevision:
    """Monotonic runtime identity for adopted authoritative Current observations."""

    value: int = 0

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("current revision must not be negative")

    def next(self) -> CurrentRevision:
        return CurrentRevision(self.value + 1)


@dataclass(frozen=True, order=True, slots=True)
class HistoryRevision:
    """Monotonic runtime invalidation token for effective History mutations."""

    value: int = 0

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("history revision must not be negative")

    def next(self) -> HistoryRevision:
        return HistoryRevision(self.value + 1)
