from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codexbar.application.ports import NotificationPort
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsagePolicy,
    UsageSnapshot,
    UsageWindowId,
    UsageWindowState,
)


@dataclass(frozen=True, slots=True)
class AlertEvent:
    window_id: UsageWindowId
    label: str
    state: UsageWindowState
    remaining: Fraction
    resets_at: datetime | None


class AlertTransitionTracker:
    """Track eligible per-window states and emit constrained-state transitions."""

    def __init__(self) -> None:
        self._states: dict[UsageWindowId, UsageWindowState] = {}

    def evaluate(
        self,
        snapshot: UsageSnapshot,
        policy: UsagePolicy,
    ) -> tuple[AlertEvent, ...]:
        if snapshot.freshness is not Freshness.CURRENT:
            return ()

        events: list[AlertEvent] = []
        for window in snapshot.windows:
            current = window.state(policy)
            previous = self._states.get(window.id)
            self._states[window.id] = current

            if previous is None or previous is current:
                continue
            if current not in {UsageWindowState.LOW, UsageWindowState.EXHAUSTED}:
                continue

            events.append(
                AlertEvent(
                    window_id=window.id,
                    label=window.label,
                    state=current,
                    remaining=window.remaining,
                    resets_at=window.resets_at,
                )
            )

        return tuple(events)


class AlertService:
    """Apply notification enablement while always advancing eligible transition state."""

    def __init__(
        self,
        notifier: NotificationPort,
        tracker: AlertTransitionTracker | None = None,
    ) -> None:
        self._notifier = notifier
        self._tracker = tracker or AlertTransitionTracker()

    def process(
        self,
        snapshot: UsageSnapshot,
        policy: UsagePolicy,
        *,
        notifications_enabled: bool,
    ) -> tuple[AlertEvent, ...]:
        events = self._tracker.evaluate(snapshot, policy)
        if not notifications_enabled:
            return events

        for event in events:
            try:
                self._notifier.notify(event)
            except NotificationDeliveryError:
                continue
        return events
