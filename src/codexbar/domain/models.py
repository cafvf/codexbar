from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Fraction:
    """Dimensionless fraction constrained to the closed interval [0, 1]."""

    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or not Decimal("0") <= self.value <= Decimal("1"):
            raise ValueError("fraction must be finite and between 0 and 1")

    @classmethod
    def from_percent(cls, percent: Decimal) -> Fraction:
        return cls(percent / Decimal("100"))

    @property
    def percent(self) -> Decimal:
        return self.value * Decimal("100")


@dataclass(frozen=True, slots=True)
class UsageWindowId:
    """Opaque stable identifier assigned by an infrastructure adapter."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("usage window id must not be blank")


class UsageWindowState(StrEnum):
    AVAILABLE = "available"
    LOW = "low"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class UsagePolicy:
    """Presentation-oriented policy kept explicit instead of hidden constants."""

    low_remaining_threshold: Fraction = Fraction(Decimal("0.20"))


DEFAULT_USAGE_POLICY = UsagePolicy()


@dataclass(frozen=True, slots=True)
class UsageWindow:
    id: UsageWindowId
    label: str
    remaining: Fraction
    resets_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("usage window label must not be blank")
        if self.resets_at is not None and (
            self.resets_at.tzinfo is None or self.resets_at.utcoffset() is None
        ):
            raise ValueError("resets_at must be timezone-aware")

    def state(self, policy: UsagePolicy = DEFAULT_USAGE_POLICY) -> UsageWindowState:
        if self.remaining.value == 0:
            return UsageWindowState.EXHAUSTED
        if self.remaining.value <= policy.low_remaining_threshold.value:
            return UsageWindowState.LOW
        return UsageWindowState.AVAILABLE


class UsageSource(StrEnum):
    MOCK = "mock"
    CODEX_APP_SERVER = "codex_app_server"


class Freshness(StrEnum):
    CURRENT = "current"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    windows: tuple[UsageWindow, ...]
    observed_at: datetime
    source: UsageSource
    freshness: Freshness = Freshness.CURRENT
    rate_limit_reached_type: str | None = None

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")

        ids = [window.id.value for window in self.windows]
        if len(ids) != len(set(ids)):
            raise ValueError("usage window ids must be unique within a snapshot")

    def as_stale(self) -> UsageSnapshot:
        return replace(self, freshness=Freshness.STALE)
