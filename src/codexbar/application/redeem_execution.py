from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from typing import Protocol

from codexbar.application.redeem import RedeemResult
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.diagnostics import RuntimeMetricCollector
from codexbar.domain.reset import ResetCreditId


class RedeemExecutor(Protocol):
    def redeem(self, *, credit_id: ResetCreditId | None = None) -> RedeemResult: ...

    def retry(self, attempt_id: RedeemAttemptId) -> RedeemResult: ...


class RedeemExecutionPhase(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    RESULT = "result"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class RedeemExecutionState:
    phase: RedeemExecutionPhase
    generation: int
    result: RedeemResult | None = None
    error: str | None = None


class RedeemExecutionController:
    """Async UI orchestration around the unchanged durable RedeemProcessManager."""

    def __init__(
        self,
        manager: RedeemExecutor,
        executor: Executor | None = None,
        *,
        runtime_metrics: RuntimeMetricCollector | None = None,
    ) -> None:
        self._manager = manager
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="codexbar-redeem",
        )
        self._owns_executor = executor is None
        self._metrics = runtime_metrics
        self._future: Future[RedeemResult] | None = None
        self._future_generation: int | None = None
        self._generation = 0
        self._active_generation = 0
        self._state = RedeemExecutionState(RedeemExecutionPhase.IDLE, generation=0)
        self._closed = False
        self._lock = Lock()

    @property
    def state(self) -> RedeemExecutionState:
        return self._state

    @property
    def busy(self) -> bool:
        future = self._future
        return future is not None

    def start_redeem(self, *, credit_id: ResetCreditId | None = None) -> bool:
        return self._start(lambda: self._manager.redeem(credit_id=credit_id))

    def start_retry(self, attempt_id: RedeemAttemptId) -> bool:
        return self._start(lambda: self._manager.retry(attempt_id))

    def poll(self) -> RedeemExecutionState:
        with self._measure("redeem.ui_poll"):
            future = self._future
            if future is None or not future.done():
                return self._state

            generation = self._future_generation
            self._future = None
            self._future_generation = None
            try:
                result = future.result()
            except Exception as exc:  # Durable/process-manager semantics already ran in worker.
                with self._lock:
                    if self._closed or generation != self._active_generation:
                        return self._state
                    self._state = RedeemExecutionState(
                        RedeemExecutionPhase.ERROR,
                        generation=self._active_generation,
                        error=str(exc),
                    )
                    return self._state

            with self._lock:
                if self._closed or generation != self._active_generation:
                    return self._state
                self._state = RedeemExecutionState(
                    RedeemExecutionPhase.RESULT,
                    generation=self._active_generation,
                    result=result,
                )
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

    def _start(self, action: Callable[[], RedeemResult]) -> bool:
        with self._measure("redeem.ui_submit"), self._lock:
            if self._closed or self.busy:
                return False
            self._generation += 1
            generation = self._generation
            self._active_generation = generation
            self._state = RedeemExecutionState(
                RedeemExecutionPhase.RUNNING,
                generation=generation,
            )
            self._future = self._executor.submit(self._execute, action)
            self._future_generation = generation
            return True

    def _execute(self, action: Callable[[], RedeemResult]) -> RedeemResult:
        with self._measure("redeem.background"):
            return action()

    def _measure(self, operation: str) -> AbstractContextManager[None]:
        metrics = self._metrics
        return metrics.measure(operation) if metrics is not None else nullcontext()
