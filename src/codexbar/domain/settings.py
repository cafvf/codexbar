from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from codexbar.domain.models import Fraction, UsagePolicy, UsageWindowId
from codexbar.domain.quantities import TimeToReset

MIN_REFRESH_INTERVAL_SECONDS = 10
MAX_REFRESH_INTERVAL_SECONDS = 3600
DEFAULT_REFRESH_INTERVAL_SECONDS = 60
DEFAULT_LOW_REMAINING_THRESHOLD = Fraction(Decimal("0.20"))
DEFAULT_NOTIFICATIONS_ENABLED = True
DEFAULT_PLAN_BREACH_NOTIFICATIONS_ENABLED = False


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
        return UsageReservePolicy(tuple(by_id[key] for key in sorted(by_id)))


def _checkpoint_seconds(time_to_reset: TimeToReset) -> int:
    duration = time_to_reset.duration
    if duration.microseconds != 0:
        raise ValueError("plan checkpoint time to reset must use whole seconds")
    return duration.days * 86_400 + duration.seconds


@dataclass(frozen=True, slots=True)
class UsagePlanCheckpoint:
    """One explicit minimum-remaining target at a factual time-to-reset coordinate."""

    window_id: UsageWindowId
    time_to_reset: TimeToReset
    minimum_remaining: Fraction

    def __post_init__(self) -> None:
        _checkpoint_seconds(self.time_to_reset)


@dataclass(frozen=True, slots=True)
class UsagePlanCheckpointPolicy:
    """Immutable canonical checkpoint policy keyed by opaque usage-window identity."""

    entries: tuple[UsagePlanCheckpoint, ...] = ()

    def __post_init__(self) -> None:
        coordinates = [
            (entry.window_id.value, _checkpoint_seconds(entry.time_to_reset))
            for entry in self.entries
        ]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError("plan checkpoint coordinates must be unique per usage window")

        canonical = tuple(
            sorted(
                self.entries,
                key=lambda entry: (
                    entry.window_id.value,
                    -_checkpoint_seconds(entry.time_to_reset),
                ),
            )
        )
        object.__setattr__(self, "entries", canonical)

    def checkpoints_for(
        self,
        window_id: UsageWindowId,
    ) -> tuple[UsagePlanCheckpoint, ...]:
        return tuple(entry for entry in self.entries if entry.window_id == window_id)


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Validated user-configurable behavior independent of persistence and UI."""

    low_remaining_threshold: Fraction
    refresh_interval_seconds: RefreshIntervalSeconds
    notifications_enabled: bool
    usage_reserves: UsageReservePolicy = UsageReservePolicy()
    usage_plan_checkpoints: UsagePlanCheckpointPolicy = UsagePlanCheckpointPolicy()
    plan_breach_notifications_enabled: bool = DEFAULT_PLAN_BREACH_NOTIFICATIONS_ENABLED

    def __post_init__(self) -> None:
        if not Decimal("0") < self.low_remaining_threshold.value < Decimal("1"):
            raise ValueError("low remaining threshold must be strictly between 0 and 1")
        if not isinstance(self.notifications_enabled, bool):
            raise ValueError("notifications_enabled must be a boolean")
        if not isinstance(self.plan_breach_notifications_enabled, bool):
            raise ValueError("plan_breach_notifications_enabled must be a boolean")

    @classmethod
    def defaults(cls) -> AppSettings:
        return cls(
            low_remaining_threshold=DEFAULT_LOW_REMAINING_THRESHOLD,
            refresh_interval_seconds=RefreshIntervalSeconds(DEFAULT_REFRESH_INTERVAL_SECONDS),
            notifications_enabled=DEFAULT_NOTIFICATIONS_ENABLED,
            usage_reserves=UsageReservePolicy(),
            usage_plan_checkpoints=UsagePlanCheckpointPolicy(),
            plan_breach_notifications_enabled=DEFAULT_PLAN_BREACH_NOTIFICATIONS_ENABLED,
        )

    def usage_policy(self) -> UsagePolicy:
        return UsagePolicy(low_remaining_threshold=self.low_remaining_threshold)

    def with_usage_reserve(
        self,
        window_id: UsageWindowId,
        reserve: Fraction | None,
    ) -> AppSettings:
        return replace(
            self,
            usage_reserves=self.usage_reserves.with_reserve(window_id, reserve),
        )

    def with_usage_plan_checkpoints(
        self,
        policy: UsagePlanCheckpointPolicy,
    ) -> AppSettings:
        return replace(self, usage_plan_checkpoints=policy)

    def with_plan_breach_notifications_enabled(self, enabled: bool) -> AppSettings:
        return replace(self, plan_breach_notifications_enabled=enabled)
