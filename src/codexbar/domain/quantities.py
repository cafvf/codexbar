from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True, order=True)
class TimeToReset:
    """Non-negative time remaining until an authoritative reset instant."""

    duration: timedelta

    def __post_init__(self) -> None:
        if self.duration < timedelta(0):
            raise ValueError("time to reset must not be negative")

    @classmethod
    def from_instants(cls, *, observed_at: datetime, resets_at: datetime) -> TimeToReset:
        observed_utc = _require_aware(observed_at, "observed_at")
        reset_utc = _require_aware(resets_at, "resets_at")
        return cls(reset_utc - observed_utc)


@dataclass(frozen=True, slots=True)
class FractionDelta:
    """Signed difference between two normalized fractions."""

    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite():
            raise ValueError("fraction delta must be a finite Decimal")
