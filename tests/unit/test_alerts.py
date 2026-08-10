from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.alerts import AlertEvent, AlertService, AlertTransitionTracker
from codexbar.application.notifications import NotificationMessage
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsagePolicy,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
    UsageWindowState,
)

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


class RecordingNotifier:
    def __init__(self, *, fail: bool = False) -> None:
        self.events: list[NotificationMessage] = []
        self.fail = fail

    def notify(self, message: NotificationMessage) -> None:
        self.events.append(message)
        if self.fail:
            raise NotificationDeliveryError("notification transport failed")


def snapshot(
    *remaining: tuple[str, str, str],
    freshness: Freshness = Freshness.CURRENT,
) -> UsageSnapshot:
    return UsageSnapshot(
        windows=tuple(
            UsageWindow(
                UsageWindowId(window_id),
                label,
                Fraction(Decimal(value)),
            )
            for window_id, label, value in remaining
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def policy(threshold: str = "0.20") -> UsagePolicy:
    return UsagePolicy(low_remaining_threshold=Fraction(Decimal(threshold)))


def test_first_current_snapshot_is_silent_baseline_even_when_constrained() -> None:
    tracker = AlertTransitionTracker()

    events = tracker.evaluate(
        snapshot(("weekly", "Weekly", "0.10"), ("five_hour", "5 hours", "0")),
        policy(),
    )

    assert events == ()


def test_available_to_low_emits_one_event_with_normalized_window_data() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())

    events = tracker.evaluate(snapshot(("weekly", "Weekly", "0.15")), policy())

    assert events == (
        AlertEvent(
            window_id=UsageWindowId("weekly"),
            label="Weekly",
            state=UsageWindowState.LOW,
            remaining=Fraction(Decimal("0.15")),
            resets_at=None,
        ),
    )


def test_available_to_exhausted_and_low_to_exhausted_are_alertable() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(
        snapshot(
            ("weekly", "Weekly", "0.50"),
            ("five_hour", "5 hours", "0.10"),
        ),
        policy(),
    )

    events = tracker.evaluate(
        snapshot(
            ("weekly", "Weekly", "0"),
            ("five_hour", "5 hours", "0"),
        ),
        policy(),
    )

    assert [event.window_id.value for event in events] == ["weekly", "five_hour"]
    assert [event.state for event in events] == [
        UsageWindowState.EXHAUSTED,
        UsageWindowState.EXHAUSTED,
    ]


def test_exhausted_to_low_is_new_alertable_state() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0")), policy())

    events = tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())

    assert len(events) == 1
    assert events[0].state is UsageWindowState.LOW


def test_unchanged_constrained_state_is_deduplicated() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())
    first = tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())
    second = tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())

    assert len(first) == 1
    assert second == ()


def test_recovery_rearms_later_low_transition_without_alerting_on_recovery() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())

    recovery = tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())
    later = tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())

    assert recovery == ()
    assert len(later) == 1
    assert later[0].state is UsageWindowState.LOW


def test_new_window_gets_silent_baseline_and_absence_does_not_rearm() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())

    added = tracker.evaluate(
        snapshot(
            ("weekly", "Weekly", "0.50"),
            ("five_hour", "5 hours", "0.10"),
        ),
        policy(),
    )
    absent = tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())
    returned = tracker.evaluate(
        snapshot(
            ("weekly", "Weekly", "0.50"),
            ("five_hour", "5 hours", "0.10"),
        ),
        policy(),
    )

    assert added == ()
    assert absent == ()
    assert returned == ()


def test_stale_snapshot_neither_alerts_nor_advances_state() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot(("weekly", "Weekly", "0.50")), policy())

    stale = tracker.evaluate(
        snapshot(("weekly", "Weekly", "0.10"), freshness=Freshness.STALE),
        policy(),
    )
    current = tracker.evaluate(snapshot(("weekly", "Weekly", "0.10")), policy())

    assert stale == ()
    assert len(current) == 1
    assert current[0].state is UsageWindowState.LOW


def test_multiple_transitions_preserve_snapshot_order() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(
        snapshot(
            ("weekly", "Weekly", "0.50"),
            ("five_hour", "5 hours", "0.50"),
        ),
        policy(),
    )

    events = tracker.evaluate(
        snapshot(
            ("five_hour", "5 hours", "0.10"),
            ("weekly", "Weekly", "0"),
        ),
        policy(),
    )

    assert [event.window_id.value for event in events] == ["five_hour", "weekly"]


def test_disabled_notifications_advance_state_without_delivery_or_replay() -> None:
    notifier = RecordingNotifier()
    service = AlertService(notifier)
    service.process(
        snapshot(("weekly", "Weekly", "0.50")),
        policy(),
        notifications_enabled=False,
    )
    suppressed = service.process(
        snapshot(("weekly", "Weekly", "0.10")),
        policy(),
        notifications_enabled=False,
    )
    replay = service.process(
        snapshot(("weekly", "Weekly", "0.10")),
        policy(),
        notifications_enabled=True,
    )

    assert len(suppressed) == 1
    assert replay == ()
    assert notifier.events == []


def test_reenabled_notifications_deliver_a_later_new_transition() -> None:
    notifier = RecordingNotifier()
    service = AlertService(notifier)
    service.process(
        snapshot(("weekly", "Weekly", "0.50")),
        policy(),
        notifications_enabled=False,
    )
    service.process(
        snapshot(("weekly", "Weekly", "0.10")),
        policy(),
        notifications_enabled=False,
    )
    service.process(
        snapshot(("weekly", "Weekly", "0.50")),
        policy(),
        notifications_enabled=True,
    )
    service.process(
        snapshot(("weekly", "Weekly", "0")),
        policy(),
        notifications_enabled=True,
    )

    assert len(notifier.events) == 1
    assert notifier.events[0].summary == "CodexBar usage exhausted"


def test_normalized_delivery_failure_is_contained() -> None:
    notifier = RecordingNotifier(fail=True)
    service = AlertService(notifier)
    service.process(
        snapshot(("weekly", "Weekly", "0.50")),
        policy(),
        notifications_enabled=True,
    )

    events = service.process(
        snapshot(("weekly", "Weekly", "0.10")),
        policy(),
        notifications_enabled=True,
    )

    assert len(events) == 1
    assert len(notifier.events) == 1
