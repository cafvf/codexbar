from __future__ import annotations

import json
from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from codexbar.application.alerts import AlertEvent, AlertService
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import NotificationDeliveryError, UsageSourceError
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
from codexbar.domain.settings import AppSettings
from codexbar.infrastructure.settings import JsonSettingsRepository
from codexbar.ui.controller import TrayController, TrayPhase

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:
            future.set_exception(exc)
        return future


class SequenceProvider:
    def __init__(self, outcomes: list[UsageSnapshot | Exception]) -> None:
        self._outcomes = iter(outcomes)

    def get_usage(self) -> UsageSnapshot:
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FailingThenRecordingNotifier:
    def __init__(self) -> None:
        self.attempts: list[AlertEvent] = []

    def notify(self, event: AlertEvent) -> None:
        self.attempts.append(event)
        if len(self.attempts) == 1:
            raise NotificationDeliveryError("expected test failure")


def snapshot(remaining: str, *, freshness: Freshness = Freshness.CURRENT) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal(remaining)),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def refresh_once(controller: TrayController) -> None:
    assert controller.start_refresh()
    controller.poll()


def test_inv_alert_004_settings_save_preserves_alert_values_in_schema_v2(
    tmp_path: Path,
) -> None:
    repository = JsonSettingsRepository(
        env={"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    )
    repository.save(AppSettings.defaults())

    payload = json.loads(repository.path.read_text(encoding="utf-8"))

    assert payload == {
        "schema_version": 2,
        "low_remaining_threshold": "0.20",
        "refresh_interval_seconds": 60,
        "notifications_enabled": True,
        "usage_reserves": {},
    }


def test_inv_alert_005_configured_policy_controls_transition_classification() -> None:
    notifier = FailingThenRecordingNotifier()
    service = AlertService(notifier)
    policy = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.15")))

    service.process(snapshot("0.50"), policy, notifications_enabled=True)
    at_eighteen = service.process(snapshot("0.18"), policy, notifications_enabled=True)
    at_fifteen = service.process(snapshot("0.15"), policy, notifications_enabled=True)

    assert at_eighteen == ()
    assert len(at_fifteen) == 1
    assert at_fifteen[0].state is UsageWindowState.LOW


def test_ac_alert_021_stale_state_does_not_replace_last_current_state() -> None:
    notifier = FailingThenRecordingNotifier()
    service = AlertService(notifier)
    policy = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.20")))

    service.process(snapshot("0.50"), policy, notifications_enabled=False)
    service.process(
        snapshot("0.10", freshness=Freshness.STALE),
        policy,
        notifications_enabled=False,
    )
    events = service.process(snapshot("0.10"), policy, notifications_enabled=False)

    assert len(events) == 1
    assert events[0].state is UsageWindowState.LOW


def test_ac_alert_024_delivery_failure_does_not_replace_fresh_tray_state() -> None:
    notifier = FailingThenRecordingNotifier()
    provider = SequenceProvider([snapshot("0.50"), snapshot("0.10")])
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(provider)),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    refresh_once(controller)

    assert controller.state.phase is TrayPhase.FRESH
    assert controller.state.usage is not None
    assert controller.state.usage.windows[0].state is UsageWindowState.LOW
    assert len(notifier.attempts) == 1


def test_ac_alert_025_delivery_failure_does_not_prevent_later_attempt() -> None:
    notifier = FailingThenRecordingNotifier()
    provider = SequenceProvider(
        [
            snapshot("0.50"),
            snapshot("0.10"),
            snapshot("0.50"),
            snapshot("0"),
        ]
    )
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(provider)),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    for _ in range(4):
        refresh_once(controller)

    assert len(notifier.attempts) == 2
    assert notifier.attempts[-1].state is UsageWindowState.EXHAUSTED
    assert controller.state.phase is TrayPhase.FRESH


def test_refresh_error_becomes_stale_without_fabricating_alert_transition() -> None:
    notifier = FailingThenRecordingNotifier()
    provider = SequenceProvider(
        [
            snapshot("0.50"),
            UsageSourceError("provider unavailable"),
            snapshot("0.10"),
        ]
    )
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(provider)),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    refresh_once(controller)

    assert controller.state.phase is TrayPhase.STALE
    assert controller.state.usage is not None
    assert controller.state.usage.stale is True
    assert notifier.attempts == []

    refresh_once(controller)

    assert controller.state.phase is TrayPhase.FRESH
    assert len(notifier.attempts) == 1
    assert notifier.attempts[0].state is UsageWindowState.LOW
