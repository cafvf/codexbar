import re
from dataclasses import dataclass
from datetime import datetime

from codexbar.domain.models import (
    DEFAULT_USAGE_POLICY,
    Freshness,
    UsagePolicy,
    UsageSnapshot,
    UsageWindow,
    UsageWindowId,
    UsageWindowState,
)


@dataclass(frozen=True, slots=True)
class UsageWindowViewState:
    window_id: UsageWindowId
    label: str
    short_label: str
    percent_left: int
    reset_at: datetime | None
    state: UsageWindowState


@dataclass(frozen=True, slots=True)
class UsageViewState:
    windows: tuple[UsageWindowViewState, ...]
    observed_at: datetime
    stale: bool
    rate_limit_reached_type: str | None
    glance_text: str


class UsageViewModel:
    @staticmethod
    def from_snapshot(
        snapshot: UsageSnapshot,
        policy: UsagePolicy = DEFAULT_USAGE_POLICY,
    ) -> UsageViewState:
        windows = tuple(
            UsageWindowViewState(
                window_id=window.id,
                label=window.label,
                short_label=_short_window_label(window),
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
            glance_text=_format_glance_text(windows),
        )


def _short_window_label(window: UsageWindow) -> str:
    """Return a stable compact label derived from the canonical window id when possible."""

    match = re.fullmatch(r"window_(\d+)m", window.id.value)
    if match is not None:
        duration_minutes = int(match.group(1))
        if duration_minutes == 300:
            return "5h"
        if duration_minutes == 10_080:
            return "W"
        if duration_minutes % (24 * 60) == 0:
            return f"{duration_minutes // (24 * 60)}d"
        if duration_minutes % 60 == 0:
            return f"{duration_minutes // 60}h"
        return f"{duration_minutes}m"

    normalized = window.label.strip().lower()
    if normalized in {"5 hours", "5 hour", "5h"}:
        return "5h"
    if normalized in {"weekly", "week", "w"}:
        return "W"
    return window.label.strip()


def _format_glance_text(windows: tuple[UsageWindowViewState, ...]) -> str:
    return " · ".join(
        f"{window.short_label}: {window.percent_left}%"
        for window in windows
    )
