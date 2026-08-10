from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from codexbar.application.analytics import AnalysisPeriod, HistoricalAnalysisService
from codexbar.application.history import (
    HistoricalWindowObservation,
    HistoricalWindowSample,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_viewmodel import HistoryViewPhase

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
A = UsageWindowId("a")
B = UsageWindowId("b")


class Repo:
    def query_window(self, window_id, interval):
        value = Decimal("0.40") if window_id == A else Decimal("0.70")
        return (
            HistoricalWindowSample(
                observed_at=interval.end - timedelta(minutes=1),
                source=UsageSource.MOCK,
                observation=HistoricalWindowObservation(
                    window_id=window_id,
                    label=window_id.value.upper(),
                    remaining=Fraction(value),
                ),
            ),
        )

    def list_window_ids(self, interval):
        return (A, B)


class QueuedExecutor(Executor):
    def __init__(self) -> None:
        self.jobs: list[tuple[Future[Any], Callable[[], Any]]] = []
        self.shutdown_called = False

    def submit(self, fn, /, *args, **kwargs):
        future: Future[Any] = Future()
        self.jobs.append((future, lambda: fn(*args, **kwargs)))
        return future

    def run(self, index: int) -> None:
        future, job = self.jobs[index]
        if future.set_running_or_notify_cancel():
            try:
                future.set_result(job())
            except BaseException as exc:
                future.set_exception(exc)

    def shutdown(self, wait=True, *, cancel_futures=False):
        self.shutdown_called = True
        if cancel_futures:
            for future, _ in self.jobs:
                future.cancel()


def test_default_request_selects_first_analyzable_window() -> None:
    executor = QueuedExecutor()
    controller = HistoryController(
        HistoricalAnalysisService(Repo()),
        executor,
        clock=lambda: T0,
    )

    assert controller.start()
    assert controller.state.phase is HistoryViewPhase.LOADING
    executor.run(0)
    state = controller.poll()

    assert state.phase is HistoryViewPhase.READY
    assert state.period is AnalysisPeriod.HOURS_24
    assert state.selected_window_id == A


def test_requested_window_is_preserved_when_available() -> None:
    executor = QueuedExecutor()
    controller = HistoryController(
        HistoricalAnalysisService(Repo()),
        executor,
        clock=lambda: T0,
    )

    controller.start(AnalysisPeriod.DAYS_7, window_id=B)
    executor.run(0)
    state = controller.poll()

    assert state.selected_window_id == B
    assert state.period is AnalysisPeriod.DAYS_7


def test_newer_request_supersedes_older_completion() -> None:
    executor = QueuedExecutor()
    controller = HistoryController(
        HistoricalAnalysisService(Repo()),
        executor,
        clock=lambda: T0,
    )

    controller.start(AnalysisPeriod.DAYS_30, window_id=A)
    controller.start(AnalysisPeriod.HOURS_24, window_id=B)

    executor.run(0)
    assert controller.state.phase is HistoryViewPhase.LOADING
    assert controller.poll().phase is HistoryViewPhase.LOADING

    executor.run(1)
    state = controller.poll()
    assert state.phase is HistoryViewPhase.READY
    assert state.period is AnalysisPeriod.HOURS_24
    assert state.selected_window_id == B


def test_close_ignores_outstanding_completion() -> None:
    executor = QueuedExecutor()
    controller = HistoryController(
        HistoricalAnalysisService(Repo()),
        executor,
        clock=lambda: T0,
    )

    controller.start(window_id=A)
    controller.close()
    executor.run(0)

    assert controller.poll().phase is HistoryViewPhase.LOADING
    assert not controller.start(window_id=B)


def test_controller_uses_one_captured_end_for_discovery_and_analysis() -> None:
    clock_values = iter(
        (
            T0,
            T0 + timedelta(hours=5),
        )
    )
    executor = QueuedExecutor()
    controller = HistoryController(
        HistoricalAnalysisService(Repo()),
        executor,
        clock=lambda: next(clock_values),
    )

    controller.start(window_id=A)
    executor.run(0)
    state = controller.poll()

    assert state.summary is not None
    assert state.summary.latest_observed_at == T0 - timedelta(minutes=1)
