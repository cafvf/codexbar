from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import UsageSourceUnavailableError
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.ui.controller import TrayController, TrayPhase


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # test executor mirrors Future semantics
            future.set_exception(exc)
        return future


class PendingExecutor:
    def __init__(self) -> None:
        self.future: Future[object] = Future()

    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        return self.future


class SequenceProvider:
    def __init__(self, values: list[UsageSnapshot | Exception]) -> None:
        self._values = iter(values)

    def get_usage(self) -> UsageSnapshot:
        value = next(self._values)
        if isinstance(value, Exception):
            raise value
        return value


def snapshot(percent_left: str = "75") -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                id=UsageWindowId("weekly"),
                label="Weekly",
                remaining=Fraction.from_percent(Decimal(percent_left)),
            ),
        ),
        observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        source=UsageSource.MOCK,
    )


def test_ac_ui_001_refresh_enters_loading_without_blocking_caller() -> None:
    executor = PendingExecutor()
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(SequenceProvider([snapshot()]))),
        executor=executor,
    )

    assert controller.start_refresh() is True
    assert controller.state.phase is TrayPhase.LOADING
    assert controller.busy is True


def test_ac_ui_002_successful_refresh_becomes_fresh_and_maps_usage() -> None:
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(SequenceProvider([snapshot("81")]))),
        executor=ImmediateExecutor(),
    )

    controller.start_refresh()
    state = controller.poll()

    assert state.phase is TrayPhase.FRESH
    assert state.usage is not None
    assert state.usage.windows[0].percent_left == 81


def test_ac_ui_003_transient_failure_after_success_exposes_stale_state() -> None:
    provider = SequenceProvider([snapshot("63"), UsageSourceUnavailableError("offline")])
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(provider)),
        executor=ImmediateExecutor(),
    )

    controller.start_refresh()
    assert controller.poll().phase is TrayPhase.FRESH
    controller.start_refresh()
    state = controller.poll()

    assert state.phase is TrayPhase.STALE
    assert state.usage is not None
    assert state.usage.windows[0].percent_left == 63


def test_ac_ui_004_initial_failure_exposes_error_without_fabricated_usage() -> None:
    controller = TrayController(
        RefreshCoordinator(
            GetCurrentUsage(SequenceProvider([UsageSourceUnavailableError("codex unavailable")]))
        ),
        executor=ImmediateExecutor(),
    )

    controller.start_refresh()
    state = controller.poll()

    assert state.phase is TrayPhase.ERROR
    assert state.usage is None
    assert state.message == "codex unavailable"


def test_ac_ui_005_overlapping_refresh_is_rejected() -> None:
    executor = PendingExecutor()
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(SequenceProvider([snapshot()]))),
        executor=executor,
    )

    assert controller.start_refresh() is True
    assert controller.start_refresh() is False
