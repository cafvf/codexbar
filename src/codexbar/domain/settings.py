from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from codexbar.domain.models import Fraction, UsagePolicy, UsageWindowId

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
class UsageReserve:
    """Remaining-quota reserve bound only to one stable usage-window identity."""

    window_id: UsageWindowId
    reserve: Fraction


@dataclass(frozen=True, slots=True)
class UsageReservePolicy:
    """Immutable per-window reserve policy."""

    entries: tuple[UsageReserve, ...] = ()

    def __post_init__(self) -> None:
        ids = [entry.window_id.value for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("usage reserve window ids must be unique")

    def reserve_for(self, window_id: UsageWindowId) -> Fraction | None:
        for entry in self.entries:
            if entry.window_id == window_id:
                return entry.reserve
        return None

    def with_reserve(
        self,
        window_id: UsageWindowId,
        reserve: Fraction | None,
    ) -> UsageReservePolicy:
        by_id = {entry.window_id.value: entry for entry in self.entries}
        if reserve is None:
            by_id.pop(window_id.value, None)
        else:
            by_id[window_id.value] = UsageReserve(window_id, reserve)
        return UsageReservePolicy(
            tuple(by_id[key] for key in sorted(by_id))
        )


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Validated user-configurable behavior independent of persistence and UI."""

    low_remaining_threshold: Fraction
    refresh_interval_seconds: RefreshIntervalSeconds
    notifications_enabled: bool
    usage_reserves: UsageReservePolicy = UsageReservePolicy()

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
            usage_reserves=UsageReservePolicy(),
        )

    def usage_policy(self) -> UsagePolicy:
        return UsagePolicy(low_remaining_threshold=self.low_remaining_threshold)

    def with_usage_reserve(
        self,
        window_id: UsageWindowId,
        reserve: Fraction | None,
    ) -> AppSettings:
        return AppSettings(
            low_remaining_threshold=self.low_remaining_threshold,
            refresh_interval_seconds=self.refresh_interval_seconds,
            notifications_enabled=self.notifications_enabled,
            usage_reserves=self.usage_reserves.with_reserve(window_id, reserve),
        )
