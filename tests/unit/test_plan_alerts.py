from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.notifications import NotificationMessage
from codexbar.application.plan_alerts import PlanAlertService
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import (
    AppSettings,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
)

BASE = datetime(2026, 8, 14, 12, tzinfo=UTC)
WEEKLY = UsageWindowId("opaque-weekly")
SHORT = UsageWindowId("opaque-short")


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def notify(self, message: NotificationMessage) -> None:
        self.messages.append(message)


class FailingNotifier:
    def __init__(self) -> None:
        self.attempts = 0

    def notify(self, message: NotificationMessage) -> None:
        del message
        self.attempts += 1
        raise NotificationDeliveryError("expected delivery failure")


def f(value: str) -> Fraction:
    return Fraction(Decimal(value))


def reserve_settings(
    reserve: str = "0.50",
    *,
    enabled: bool = True,
    window_id: UsageWindowId = WEEKLY,
) -> AppSettings:
    return (
        AppSettings.defaults()
        .with_usage_reserve(window_id, f(reserve))
        .with_plan_breach_notifications_enabled(enabled)
    )


def checkpoint_settings(
    hours: int,
    minimum: str,
    *,
    enabled: bool = True,
    reserve: str | None = None,
) -> AppSettings:
    settings = AppSettings.defaults()
    if reserve is not None:
        settings = settings.with_usage_reserve(WEEKLY, f(reserve))
    return settings.with_usage_plan_checkpoints(
        UsagePlanCheckpointPolicy(
            (
                UsagePlanCheckpoint(
                    WEEKLY,
                    TimeToReset(timedelta(hours=hours)),
                    f(minimum),
                ),
            )
        )
    ).with_plan_breach_notifications_enabled(enabled)


def snapshot(
    remaining: str,
    *,
    observed_at: datetime = BASE,
    resets_at: datetime | None = None,
    freshness: Freshness = Freshness.CURRENT,
    window_id: UsageWindowId = WEEKLY,
    label: str = "Weekly",
) -> UsageSnapshot:
    return UsageSnapshot(
        (
            UsageWindow(window_id, label, f(remaining), resets_at=resets_at),
        ),
        observed_at,
        UsageSource.MOCK,
        freshness=freshness,
    )


def test_a01_first_eligible_current_already_below_is_silent_baseline() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    events = service.process(snapshot("0.40"), notifications_enabled=True)

    assert events == ()
    assert notifier.messages == []


def test_a02_above_to_below_emits_once_and_repeated_below_is_deduplicated() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    service.process(snapshot("0.80"), notifications_enabled=True)
    first = service.process(snapshot("0.40"), notifications_enabled=True)
    repeated = service.process(snapshot("0.35"), notifications_enabled=True)

    assert len(first) == 1
    assert repeated == ()
    assert len(notifier.messages) == 1


def test_a03_recovery_rearms_later_breach() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    for remaining in ("0.80", "0.40", "0.70", "0.40"):
        service.process(snapshot(remaining), notifications_enabled=True)

    assert len(notifier.messages) == 2


def test_a04_disabled_gates_advance_tracker_without_replay() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings(enabled=False))

    service.process(snapshot("0.80"), notifications_enabled=True)
    suppressed = service.process(snapshot("0.40"), notifications_enabled=True)
    service.apply_settings(reserve_settings(enabled=True))
    replay = service.process(snapshot("0.40"), notifications_enabled=True)

    assert len(suppressed) == 1
    assert replay == ()
    assert notifier.messages == []

    service.process(snapshot("0.70"), notifications_enabled=True)
    service.process(snapshot("0.40"), notifications_enabled=False)
    service.process(snapshot("0.40"), notifications_enabled=True)
    assert notifier.messages == []

    service.process(snapshot("0.70"), notifications_enabled=True)
    service.process(snapshot("0.40"), notifications_enabled=True)
    assert len(notifier.messages) == 1


def test_a05_same_cycle_checkpoint_activation_none_to_below_emits() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, checkpoint_settings(4, "0.60"))
    reset = BASE + timedelta(hours=6)

    inactive = service.process(
        snapshot("0.50", observed_at=BASE, resets_at=reset),
        notifications_enabled=True,
    )
    active = service.process(
        snapshot(
            "0.50",
            observed_at=BASE + timedelta(hours=3),
            resets_at=reset,
        ),
        notifications_enabled=True,
    )

    assert inactive == ()
    assert len(active) == 1
    assert len(notifier.messages) == 1


def test_a06_policy_edit_is_silent_rebaseline_even_when_new_policy_is_below() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings("0.30"))

    service.process(snapshot("0.40"), notifications_enabled=True)
    service.apply_settings(reserve_settings("0.50"))
    events = service.process(snapshot("0.40"), notifications_enabled=True)

    assert events == ()
    assert notifier.messages == []


def test_a07_new_resolved_reset_cycle_is_silent_rebaseline() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, checkpoint_settings(72, "0.60"))
    reset_one = BASE + timedelta(hours=48)

    service.process(
        snapshot("0.80", resets_at=reset_one),
        notifications_enabled=True,
    )
    service.process(
        snapshot("0.50", resets_at=reset_one),
        notifications_enabled=True,
    )
    assert len(notifier.messages) == 1

    observed_two = BASE + timedelta(hours=49)
    reset_two = observed_two + timedelta(hours=48)
    events = service.process(
        snapshot(
            "0.50",
            observed_at=observed_two,
            resets_at=reset_two,
        ),
        notifications_enabled=True,
    )

    assert events == ()
    assert len(notifier.messages) == 1


def test_a08_missing_or_invalid_reset_with_checkpoints_is_ineligible_and_does_not_advance() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, checkpoint_settings(72, "0.60", reserve="0.20"))
    reset = BASE + timedelta(hours=48)

    service.process(snapshot("0.80", resets_at=reset), notifications_enabled=True)
    service.process(snapshot("0.10", resets_at=None), notifications_enabled=True)
    service.process(
        snapshot("0.10", resets_at=BASE - timedelta(seconds=1)),
        notifications_enabled=True,
    )
    events = service.process(snapshot("0.10", resets_at=reset), notifications_enabled=True)

    assert len(events) == 1
    assert len(notifier.messages) == 1


def test_a09_stale_observation_neither_emits_nor_advances_tracker() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    service.process(snapshot("0.80"), notifications_enabled=True)
    stale = service.process(
        snapshot("0.40", freshness=Freshness.STALE),
        notifications_enabled=True,
    )
    current = service.process(snapshot("0.40"), notifications_enabled=True)

    assert stale == ()
    assert len(current) == 1
    assert len(notifier.messages) == 1


def test_a10_multi_window_breaches_are_independent() -> None:
    notifier = RecordingNotifier()
    settings = reserve_settings().with_usage_reserve(SHORT, f("0.50"))
    service = PlanAlertService(notifier, settings)

    baseline = UsageSnapshot(
        (
            UsageWindow(WEEKLY, "Weekly", f("0.80")),
            UsageWindow(SHORT, "5 hours", f("0.80")),
        ),
        BASE,
        UsageSource.MOCK,
    )
    breached = UsageSnapshot(
        (
            UsageWindow(WEEKLY, "Weekly", f("0.40")),
            UsageWindow(SHORT, "5 hours", f("0.30")),
        ),
        BASE + timedelta(minutes=1),
        UsageSource.MOCK,
    )

    service.process(baseline, notifications_enabled=True)
    events = service.process(breached, notifications_enabled=True)

    assert [event.window_id for event in events] == [WEEKLY, SHORT]
    assert len(notifier.messages) == 2


def test_notification_failure_is_isolated_after_tracker_advances() -> None:
    notifier = FailingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    service.process(snapshot("0.80"), notifications_enabled=True)
    events = service.process(snapshot("0.40"), notifications_enabled=True)
    repeated = service.process(snapshot("0.35"), notifications_enabled=True)

    assert len(events) == 1
    assert repeated == ()
    assert notifier.attempts == 1


def test_plan_notification_is_factual_and_contains_no_action_or_forecast() -> None:
    notifier = RecordingNotifier()
    service = PlanAlertService(notifier, reserve_settings())

    service.process(snapshot("0.80"), notifications_enabled=True)
    service.process(snapshot("0.40"), notifications_enabled=True)

    message = notifier.messages[0]
    assert message.summary == "CodexBar Plan breach"
    assert "Weekly: 40% remaining" in message.body
    assert "Plan floor 50%" in message.body
    assert "margin -10 pp" in message.body
    assert "redeem" not in message.body.lower()
    assert "will" not in message.body.lower()
    assert "forecast" not in message.body.lower()
