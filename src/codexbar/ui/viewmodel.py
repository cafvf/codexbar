from dataclasses import dataclass
from datetime import datetime

from codexbar.domain.models import (
    DEFAULT_USAGE_POLICY,
    Freshness,
    UsagePolicy,
    UsageSnapshot,
    UsageWindowState,
)


@dataclass(frozen=True, slots=True)
class UsageWindowViewState:
    label: str
    percent_left: int
    reset_at: datetime | None
    state: UsageWindowState


@dataclass(frozen=True, slots=True)
class UsageViewState:
    windows: tuple[UsageWindowViewState, ...]
    observed_at: datetime
    stale: bool
    rate_limit_reached_type: str | None


class UsageViewModel:
    @staticmethod
    def from_snapshot(
        snapshot: UsageSnapshot,
        policy: UsagePolicy = DEFAULT_USAGE_POLICY,
    ) -> UsageViewState:
        windows = tuple(
            UsageWindowViewState(
                label=window.label,
                percent_left=int(window.remaining.percent),
                reset_at=window.resets_at,
                state=window.state(policy),
            )
            for window in snapshot.windows
        )
        return UsageViewState(
            windows=windows,
            observed_at=snapshot.observed_at,
            stale=snapshot.freshness is Freshness.STALE,
            rate_limit_reached_type=snapshot.rate_limit_reached_type,
        )
