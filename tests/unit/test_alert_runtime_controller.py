from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from codexbar.application.alerts import AlertEvent, AlertService
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.ui.controller import TrayController


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:
            future.set_exception(exc)
        return future


class SequenceProvider:
    def __init__(self, remaining: list[str]) -> None:
        self._remaining = iter(remaining)

    def get_usage(self) -> UsageSnapshot:
        return UsageSnapshot(
            windows=(
                UsageWindow(
                    UsageWindowId("weekly"),
                    "Weekly",
                    Fraction(Decimal(next(self._remaining))),
                ),
            ),
            observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
            source=UsageSource.MOCK,
        )


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[AlertEvent] = []

    def notify(self, event: AlertEvent) -> None:
        self.events.append(event)


def refresh_once(controller: TrayController) -> None:
    assert controller.start_refresh() is True
    controller.poll()


def test_controller_alerts_only_after_silent_baseline_transition() -> None:
    notifier = RecordingNotifier()
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(SequenceProvider(["0.50", "0.10"]))),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    assert notifier.events == []

    refresh_once(controller)
    assert len(notifier.events) == 1


def test_live_notification_setting_suppresses_delivery_but_advances_state() -> None:
    notifier = RecordingNotifier()
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(SequenceProvider(["0.50", "0.10", "0.10", "0.50", "0.10"]))
        ),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    controller.apply_notifications_enabled(False)
    refresh_once(controller)
    controller.apply_notifications_enabled(True)
    refresh_once(controller)
    assert notifier.events == []

    refresh_once(controller)
    refresh_once(controller)
    assert len(notifier.events) == 1
