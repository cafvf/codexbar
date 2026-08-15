from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from codexbar.application.alerts import AlertService
from codexbar.application.notifications import NotificationMessage
from codexbar.application.plan_alerts import PlanAlertService
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.settings import AppSettings
from codexbar.ui.controller import TrayController, TrayPhase

NOW = datetime(2026, 8, 14, 12, tzinfo=UTC)
WINDOW_ID = UsageWindowId("opaque-weekly")


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:
            future.set_exception(exc)
        return future


class RecordingCoordinator:
    def __init__(self, refresh_values: list[UsageSnapshot] | None = None) -> None:
        self._refresh_values = iter(refresh_values or [])
        self.refresh_calls = 0
        self.accepted: list[UsageSnapshot] = []

    def refresh(self) -> UsageSnapshot:
        self.refresh_calls += 1
        return next(self._refresh_values)

    def accept_snapshot(self, snapshot: UsageSnapshot) -> UsageSnapshot:
        self.accepted.append(snapshot)
        return snapshot


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def notify(self, message: NotificationMessage) -> None:
        self.messages.append(message)


def f(value: str) -> Fraction:
    return Fraction(Decimal(value))


def snapshot(
    remaining: str,
    *,
    freshness: Freshness = Freshness.CURRENT,
) -> UsageSnapshot:
    return UsageSnapshot(
        (UsageWindow(WINDOW_ID, "Weekly", f(remaining)),),
        NOW,
        UsageSource.MOCK,
        freshness=freshness,
    )


def settings(reserve: str = "0.50", *, enabled: bool = True) -> AppSettings:
    return (
        AppSettings.defaults()
        .with_usage_reserve(WINDOW_ID, f(reserve))
        .with_plan_breach_notifications_enabled(enabled)
    )


def test_refresh_and_adopt_snapshot_share_one_plan_alert_transition_path() -> None:
    notifier = RecordingNotifier()
    config = settings()
    coordinator = RecordingCoordinator([snapshot("0.80")])
    controller = TrayController(
        coordinator,
        executor=ImmediateExecutor(),
        plan_alert_service=PlanAlertService(notifier, config),
        notifications_enabled=True,
    )

    assert controller.start_refresh()
    assert controller.poll().phase is TrayPhase.FRESH
    assert notifier.messages == []

    adopted = snapshot("0.40")
    state = controller.adopt_snapshot(adopted)

    assert state.phase is TrayPhase.FRESH
    assert coordinator.refresh_calls == 1
    assert coordinator.accepted == [adopted]
    assert [message.summary for message in notifier.messages] == [
        "CodexBar Plan breach"
    ]


def test_post_redeem_style_adoption_does_not_read_source_or_create_parallel_plan_path() -> None:
    notifier = RecordingNotifier()
    config = settings()
    coordinator = RecordingCoordinator()
    controller = TrayController(
        coordinator,
        executor=ImmediateExecutor(),
        plan_alert_service=PlanAlertService(notifier, config),
        notifications_enabled=True,
    )

    controller.adopt_snapshot(snapshot("0.80"))
    controller.adopt_snapshot(snapshot("0.40"))

    assert coordinator.refresh_calls == 0
    assert len(coordinator.accepted) == 2
    assert len(notifier.messages) == 1


def test_live_plan_settings_apply_rebaselines_silently_on_next_current_snapshot() -> None:
    notifier = RecordingNotifier()
    initial = AppSettings.defaults().with_plan_breach_notifications_enabled(True)
    coordinator = RecordingCoordinator()
    controller = TrayController(
        coordinator,
        executor=ImmediateExecutor(),
        plan_alert_service=PlanAlertService(notifier, initial),
        notifications_enabled=True,
    )

    controller.adopt_snapshot(snapshot("0.40"))
    controller.apply_plan_settings(settings("0.50"))
    controller.adopt_snapshot(snapshot("0.40"))
    assert notifier.messages == []

    controller.adopt_snapshot(snapshot("0.70"))
    controller.adopt_snapshot(snapshot("0.40"))
    assert len(notifier.messages) == 1


def test_stale_adoption_does_not_advance_plan_tracker() -> None:
    notifier = RecordingNotifier()
    config = settings()
    coordinator = RecordingCoordinator()
    controller = TrayController(
        coordinator,
        executor=ImmediateExecutor(),
        plan_alert_service=PlanAlertService(notifier, config),
        notifications_enabled=True,
    )

    controller.adopt_snapshot(snapshot("0.80"))
    stale_state = controller.adopt_snapshot(snapshot("0.40", freshness=Freshness.STALE))
    controller.adopt_snapshot(snapshot("0.40"))

    assert stale_state.phase is TrayPhase.STALE
    assert len(notifier.messages) == 1


def test_usage_low_and_plan_breach_notifications_are_independent_categories() -> None:
    notifier = RecordingNotifier()
    config = settings("0.50")
    coordinator = RecordingCoordinator()
    controller = TrayController(
        coordinator,
        executor=ImmediateExecutor(),
        usage_policy=config.usage_policy(),
        alert_service=AlertService(notifier),
        plan_alert_service=PlanAlertService(notifier, config),
        notifications_enabled=True,
    )

    controller.adopt_snapshot(snapshot("0.80"))
    controller.adopt_snapshot(snapshot("0.10"))

    assert [message.summary for message in notifier.messages] == [
        "CodexBar usage low",
        "CodexBar Plan breach",
    ]
