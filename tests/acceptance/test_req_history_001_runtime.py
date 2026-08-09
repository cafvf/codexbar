from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.alerts import AlertEvent, AlertService
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowSample,
    HistoryInspection,
    HistoryInterval,
    HistoryRepository,
    HistoryState,
    HistoryWriteError,
)
from codexbar.application.history_runtime import (
    HistoryCapturingUsageProvider,
    HistoryService,
)
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import UsageSourceError
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
    UsageWindowState,
)
from codexbar.ui.controller import TrayController, TrayPhase

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


class ImmediateExecutor:
    def submit(self, fn):
        class DoneFuture:
            def done(self) -> bool:
                return True

            def result(self):
                return fn()

        return DoneFuture()

    def shutdown(self, wait=False, *, cancel_futures=False) -> None:
        pass


class SequenceProvider:
    def __init__(self, items):
        self._items = iter(items)

    def get_usage(self):
        item = next(self._items)
        if isinstance(item, Exception):
            raise item
        return item


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[AlertEvent] = []

    def notify(self, event: AlertEvent) -> None:
        self.events.append(event)


class RecordingHistoryRepository(HistoryRepository):
    def __init__(self, *, fail_append: bool = False, fail_prune: bool = False) -> None:
        self.appended: list[HistoricalSnapshot] = []
        self.cutoffs: list[datetime] = []
        self.fail_append = fail_append
        self.fail_prune = fail_prune
        self.cleared = 0

    def append(self, snapshot: HistoricalSnapshot) -> None:
        if self.fail_append:
            raise HistoryWriteError("append failed")
        self.appended.append(snapshot)

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        return ()

    def query_window(self, window_id, interval) -> tuple[HistoricalWindowSample, ...]:
        return ()

    def prune(self, cutoff: datetime) -> int:
        self.cutoffs.append(cutoff)
        if self.fail_prune:
            raise HistoryWriteError("prune failed")
        return 0

    def inspect(self) -> HistoryInspection:
        return HistoryInspection(path="/tmp/history.sqlite3", state=HistoryState.READY_EMPTY)

    def clear(self) -> None:
        self.cleared += 1


def snapshot(remaining: str) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal(remaining)),
            ),
        ),
        observed_at=T0,
        source=UsageSource.MOCK,
    )


def refresh_once(controller: TrayController):
    assert controller.start_refresh()
    return controller.poll()


def wrapped_provider(repository, items):
    return HistoryCapturingUsageProvider(
        SequenceProvider(items),
        HistoryService(repository, clock=lambda: T0),
    )


def test_task_322_current_refresh_is_captured_and_pruned_in_worker_path() -> None:
    repository = RecordingHistoryRepository()
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(wrapped_provider(repository, [snapshot("0.80")]))),
        executor=ImmediateExecutor(),
    )

    state = refresh_once(controller)

    assert state.phase is TrayPhase.FRESH
    assert len(repository.appended) == 1
    assert repository.cutoffs == [T0 - timedelta(days=30)]


def test_task_323_provider_error_stale_fallback_is_not_captured_again() -> None:
    repository = RecordingHistoryRepository()
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(
                wrapped_provider(
                    repository,
                    [
                        snapshot("0.80"),
                        UsageSourceError("provider unavailable"),
                    ],
                )
            )
        ),
        executor=ImmediateExecutor(),
    )

    refresh_once(controller)
    state = refresh_once(controller)

    assert state.phase is TrayPhase.STALE
    assert len(repository.appended) == 1
    assert len(repository.cutoffs) == 1


def test_task_324_append_failure_does_not_break_current_state_or_alerts() -> None:
    repository = RecordingHistoryRepository(fail_append=True)
    notifier = RecordingNotifier()
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(
                wrapped_provider(
                    repository,
                    [snapshot("0.80"), snapshot("0.10")],
                )
            )
        ),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    first = refresh_once(controller)
    second = refresh_once(controller)

    assert first.phase is TrayPhase.FRESH
    assert second.phase is TrayPhase.FRESH
    assert second.usage is not None
    assert second.usage.windows[0].percent_left == 10
    assert [event.state for event in notifier.events] == [UsageWindowState.LOW]


def test_task_324_prune_failure_does_not_break_current_state_or_alerts() -> None:
    repository = RecordingHistoryRepository(fail_prune=True)
    notifier = RecordingNotifier()
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(
                wrapped_provider(
                    repository,
                    [snapshot("0.80"), snapshot("0.10")],
                )
            )
        ),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    state = refresh_once(controller)

    assert state.phase is TrayPhase.FRESH
    assert [event.state for event in notifier.events] == [UsageWindowState.LOW]


def test_ac_history_037_clear_does_not_change_current_or_alert_runtime_state() -> None:
    repository = RecordingHistoryRepository()
    notifier = RecordingNotifier()
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(
                wrapped_provider(
                    repository,
                    [
                        snapshot("0.80"),
                        snapshot("0.10"),
                        snapshot("0.09"),
                    ],
                )
            )
        ),
        executor=ImmediateExecutor(),
        alert_service=AlertService(notifier),
    )

    refresh_once(controller)
    low_state = refresh_once(controller)
    repository.clear()
    unchanged_low_state = refresh_once(controller)

    assert repository.cleared == 1
    assert low_state.phase is TrayPhase.FRESH
    assert unchanged_low_state.phase is TrayPhase.FRESH
    assert unchanged_low_state.usage is not None
    assert unchanged_low_state.usage.windows[0].percent_left == 9
    assert [event.state for event in notifier.events] == [UsageWindowState.LOW]
