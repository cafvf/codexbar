from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisService,
    HistoricalAnalysisState,
)
from codexbar.domain.models import UsageWindowId
from codexbar.ui.history_viewmodel import (
    HistoryViewState,
    history_view_from_results,
    loading_history_view,
)


@dataclass(frozen=True, slots=True)
class _HistoryRequest:
    generation: int
    period: AnalysisPeriod
    requested_window_id: UsageWindowId | None
    end: datetime


class HistoryController:
    """Framework-independent asynchronous orchestration for historical reads."""

    def __init__(
        self,
        service: HistoricalAnalysisService,
        executor: Executor | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._service = service
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="codexbar-history",
        )
        self._owns_executor = executor is None
        self._clock = clock or (lambda: datetime.now(UTC))
        self._future: Future[HistoryViewState] | None = None
        self._future_generation: int | None = None
        self._generation = 0
        self._active_generation = 0
        self._state = loading_history_view(AnalysisPeriod.HOURS_24)
        self._closed = False
        self._lock = Lock()

    @property
    def state(self) -> HistoryViewState:
        return self._state

    @property
    def busy(self) -> bool:
        future = self._future
        return future is not None and not future.done()

    def start(
        self,
        period: AnalysisPeriod = AnalysisPeriod.HOURS_24,
        *,
        window_id: UsageWindowId | None = None,
    ) -> bool:
        with self._lock:
            if self._closed:
                return False
            self._generation += 1
            request = _HistoryRequest(
                generation=self._generation,
                period=period,
                requested_window_id=window_id,
                end=self._now(),
            )
            self._active_generation = request.generation
            self._state = loading_history_view(period)
            previous_future = self._future
            if previous_future is not None and not previous_future.done():
                previous_future.cancel()
            self._future = self._executor.submit(self._execute, request)
            self._future_generation = request.generation
            return True

    def poll(self) -> HistoryViewState:
        future = self._future
        if future is None or not future.done():
            return self._state

        completed_generation = self._future_generation
        self._future = None
        self._future_generation = None
        try:
            completed = future.result()
        except Exception:
            # Expected history failures are normalized by HistoricalAnalysisService.
            # Unexpected failures remain programming errors and must not be disguised.
            raise

        with self._lock:
            if self._closed:
                return self._state
            if completed_generation != self._active_generation:
                return self._state
            self._state = completed
            return self._state

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._active_generation += 1
            future = self._future
            self._future = None
            self._future_generation = None
        if future is not None:
            future.cancel()
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def _execute(self, request: _HistoryRequest) -> HistoryViewState:
        discovery = self._service.discover(request.period, end=request.end)
        if discovery.state is not HistoricalAnalysisState.READY:
            return history_view_from_results(
                discovery,
                None,
                selected_window_id=request.requested_window_id,
            )

        selected = request.requested_window_id
        if selected is None:
            selected = discovery.window_ids[0]

        analysis = self._service.analyze(
            selected,
            request.period,
            end=request.end,
        )
        return history_view_from_results(
            discovery,
            analysis,
            selected_window_id=selected,
        )

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("history controller clock must be timezone-aware")
        return now.astimezone(UTC)

