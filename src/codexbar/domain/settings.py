from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from codexbar.domain.models import Fraction, UsagePolicy

MIN_REFRESH_INTERVAL_SECONDS = 10
MAX_REFRESH_INTERVAL_SECONDS = 3600
DEFAULT_REFRESH_INTERVAL_SECONDS = 60
DEFAULT_LOW_REMAINING_THRESHOLD = Fraction(Decimal("0.20"))
DEFAULT_NOTIFICATIONS_ENABLED = True


@dataclass(frozen=True, slots=True)
class RefreshIntervalSeconds:
    """Automatic refresh cadence constrained to the supported operational range."""

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise ValueError("refresh interval must be an integer number of seconds")
        if not MIN_REFRESH_INTERVAL_SECONDS <= self.value <= MAX_REFRESH_INTERVAL_SECONDS:
            raise ValueError(
                "refresh interval must be between "
                f"{MIN_REFRESH_INTERVAL_SECONDS} and {MAX_REFRESH_INTERVAL_SECONDS} seconds"
            )


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Validated user-configurable behavior independent of persistence and UI."""

    low_remaining_threshold: Fraction
    refresh_interval_seconds: RefreshIntervalSeconds
    notifications_enabled: bool

    def __post_init__(self) -> None:
        if not Decimal("0") < self.low_remaining_threshold.value < Decimal("1"):
            raise ValueError("low remaining threshold must be strictly between 0 and 1")
        if not isinstance(self.notifications_enabled, bool):
            raise ValueError("notifications_enabled must be a boolean")

    @classmethod
    def defaults(cls) -> AppSettings:
        return cls(
            low_remaining_threshold=DEFAULT_LOW_REMAINING_THRESHOLD,
            refresh_interval_seconds=RefreshIntervalSeconds(DEFAULT_REFRESH_INTERVAL_SECONDS),
            notifications_enabled=DEFAULT_NOTIFICATIONS_ENABLED,
        )

    def usage_policy(self) -> UsagePolicy:
        return UsagePolicy(low_remaining_threshold=self.low_remaining_threshold)
