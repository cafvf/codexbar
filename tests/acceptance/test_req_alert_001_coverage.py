from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from codexbar.application.alerts import AlertService, AlertTransitionTracker
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import UsageSourceError
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
from codexbar.ui.controller import TrayController, TrayPhase

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
RESET_AT = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


class RecordingNotifier:
    def __init__(self) -> None:
        self.events = []

    def notify(self, event) -> None:
        self.events.append(event)


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


def policy() -> UsagePolicy:
    return UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.20")))


def snapshot(
    remaining: str,
    *,
    freshness: Freshness = Freshness.CURRENT,
    resets_at: datetime | None = None,
) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal(remaining)),
                resets_at=resets_at,
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def refresh_once(controller: TrayController) -> None:
    assert controller.start_refresh()
    controller.poll()


def test_ac_alert_001_first_available_snapshot_is_silent_baseline() -> None:
    notifier = RecordingNotifier()
    service = AlertService(notifier)

    events = service.process(
        snapshot("0.80"),
        policy(),
        notifications_enabled=True,
    )

    assert events == ()
    assert notifier.events == []


def test_ac_alert_004_initial_stale_snapshot_cannot_establish_baseline() -> None:
    tracker = AlertTransitionTracker()

    stale = tracker.evaluate(
        snapshot("0.10", freshness=Freshness.STALE),
        policy(),
    )
    first_current = tracker.evaluate(snapshot("0.10"), policy())

    assert stale == ()
    assert first_current == ()


def test_ac_alert_004_and_020_initial_refresh_failure_does_not_establish_baseline() -> None:
    notifier = RecordingNotifier()
    provider = SequenceProvider(
        [
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
    assert controller.state.phase is TrayPhase.ERROR
    assert notifier.events == []

    refresh_once(controller)
    assert controller.state.phase is TrayPhase.FRESH
    assert notifier.events == []


def test_ac_alert_011_repeated_exhausted_state_is_deduplicated() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot("0.50"), policy())

    first = tracker.evaluate(snapshot("0"), policy())
    repeated = tracker.evaluate(snapshot("0"), policy())

    assert len(first) == 1
    assert first[0].state is UsageWindowState.EXHAUSTED
    assert repeated == ()


def test_ac_alert_014_new_process_tracker_creates_new_silent_baseline() -> None:
    first_process = AlertTransitionTracker()
    first_process.evaluate(snapshot("0.50"), policy())
    transition = first_process.evaluate(snapshot("0.10"), policy())
    assert len(transition) == 1

    restarted_process = AlertTransitionTracker()
    after_restart = restarted_process.evaluate(snapshot("0.10"), policy())

    assert after_restart == ()


def test_ac_alert_022_event_preserves_optional_reset_timestamp() -> None:
    tracker = AlertTransitionTracker()
    tracker.evaluate(snapshot("0.50"), policy())

    events = tracker.evaluate(
        snapshot("0.10", resets_at=RESET_AT),
        policy(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.window_id == UsageWindowId("weekly")
    assert event.label == "Weekly"
    assert event.state is UsageWindowState.LOW
    assert event.remaining == Fraction(Decimal("0.10"))
    assert event.resets_at == RESET_AT
