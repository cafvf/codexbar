from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codexbar.application.notifications import NotificationMessage, NotificationUrgency
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
                    window.id,
                    window.label,
                    current,
                    window.remaining,
                    window.resets_at,
                )
            )
        return tuple(events)


def usage_alert_message(event: AlertEvent) -> NotificationMessage:
    percent = format(event.remaining.percent.normalize(), "f")
    body = f"{event.label}: {percent}% remaining"
    if event.resets_at is not None:
        reset = event.resets_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")
        body = f"{body}. Resets {reset}."

    if event.state is UsageWindowState.EXHAUSTED:
        return NotificationMessage(
            "CodexBar usage exhausted",
            body,
            NotificationUrgency.CRITICAL,
        )
    return NotificationMessage(
        "CodexBar usage low",
        body,
        NotificationUrgency.NORMAL,
    )


class AlertService:
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
                self._notifier.notify(usage_alert_message(event))
            except NotificationDeliveryError:
                continue
        return events
