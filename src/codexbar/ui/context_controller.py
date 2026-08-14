from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from typing import Protocol

from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
)
from codexbar.ui.context_viewmodel import (
    ContextPresentationRequest,
    ContextViewState,
)


class ContextWorkSource(Protocol):
    def capture_request(self) -> ContextPresentationRequest | None: ...

    def current_identity(
        self,
    ) -> tuple[CurrentRevision, HistoryRevision] | None: ...

    def evaluate_request(self, request: ContextPresentationRequest) -> ContextViewState: ...


class ContextControllerPhase(StrEnum):
    LOADING = "loading"
    READY = "ready"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ContextControllerState:
    phase: ContextControllerPhase
    view: ContextViewState
    generation: int
    message: str | None = None
    unexpected_error: bool = False


class ContextController:
    """Framework-independent async Context orchestration with stale-result rejection."""

    def __init__(
        self,
        presenter: ContextWorkSource,
        executor: Executor | None = None,
        *,
        runtime_metrics: RuntimeMetricCollector | None = None,
    ) -> None:
        self._presenter = presenter
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="codexbar-context",
        )
        self._owns_executor = executor is None
        self._metrics = runtime_metrics
        self._future: Future[ContextViewState] | None = None
        self._future_generation: int | None = None
        self._future_request: ContextPresentationRequest | None = None
        self._last_identity: tuple[CurrentRevision, HistoryRevision] | None = None
        self._generation = 0
        self._active_generation = 0
        self._state = ContextControllerState(
            ContextControllerPhase.UNAVAILABLE,
            ContextViewState(()),
            generation=0,
            message="No current usage observation yet.",
        )
        self._closed = False
        self._lock = Lock()

    @property
    def state(self) -> ContextControllerState:
        return self._state

    @property
    def busy(self) -> bool:
        future = self._future
        return future is not None

    def start(self) -> bool:
        with self._measure("context.ui_submit"):
            request = self._presenter.capture_request()
            with self._lock:
                if self._closed:
                    return False
                self._generation += 1
                generation = self._generation
                self._active_generation = generation
                previous = self._future
                if previous is not None and not previous.done():
                    previous.cancel()
                if request is None:
                    self._future = None
                    self._future_generation = None
                    self._future_request = None
                    self._state = ContextControllerState(
                        ContextControllerPhase.UNAVAILABLE,
                        ContextViewState(()),
                        generation=generation,
                        message="No current usage observation yet.",
                    )
                    return True
                self._state = ContextControllerState(
                    ContextControllerPhase.LOADING,
                    self._state.view,
                    generation=generation,
                    message="Loading historical context…",
                )
                self._future = self._executor.submit(self._execute, request)
                self._future_generation = generation
                self._future_request = request
                return True

    def poll(self) -> ContextControllerState:
        with self._measure("context.ui_poll"):
            future = self._future
            if future is None or not future.done():
                return self._state

            generation = self._future_generation
            request = self._future_request
            self._future = None
            self._future_generation = None
            self._future_request = None
            try:
                completed = future.result()
            except Exception as exc:  # GUI boundary: expose unavailable, never resurrect.
                with self._lock:
                    if self._closed or generation != self._active_generation:
                        return self._state
                if request is not None and request.identity != self._presenter.current_identity():
                    self.start()
                    return self._state
                with self._lock:
                    if self._closed or generation != self._active_generation:
                        return self._state
                    self._state = ContextControllerState(
                        ContextControllerPhase.UNAVAILABLE,
                        ContextViewState(()),
                        generation=self._active_generation,
                        message=f"Historical context unavailable: {exc}",
                        unexpected_error=True,
                    )
                    return self._state

            if request is None:
                raise AssertionError("completed Context future must retain its request")

            with self._lock:
                if self._closed or generation != self._active_generation:
                    return self._state

            if request.identity != self._presenter.current_identity():
                self.start()
                return self._state

            with self._lock:
                if self._closed or generation != self._active_generation:
                    return self._state
                self._last_identity = request.identity
                self._state = ContextControllerState(
                    ContextControllerPhase.READY,
                    completed,
                    generation=self._active_generation,
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
            self._future_request = None
        if future is not None:
            future.cancel()
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def subsystem_health(self) -> SubsystemHealth:
        state = self._state
        request = self._future_request
        current_identity = self._presenter.current_identity()
        identity = (
            request.identity
            if request is not None
            else self._last_identity or current_identity
        )
        idle = (
            state.phase is ContextControllerPhase.UNAVAILABLE
            and not state.unexpected_error
            and current_identity is not None
        )
        phase = "idle" if idle else state.phase.value
        details = [
            DiagnosticDetail("phase", phase),
            DiagnosticDetail("generation", state.generation),
            DiagnosticDetail("busy", self.busy),
            DiagnosticDetail("revision_cache", True),
        ]
        if identity is not None:
            details.extend(
                (
                    DiagnosticDetail("current_revision", identity[0].value),
                    DiagnosticDetail("history_revision", identity[1].value),
                )
            )
        availability = (
            DiagnosticAvailability.AVAILABLE
            if idle
            or state.phase in {
                ContextControllerPhase.LOADING,
                ContextControllerPhase.READY,
            }
            else DiagnosticAvailability.UNAVAILABLE
        )
        health = OperationalHealth.DEGRADED if state.unexpected_error else OperationalHealth.OK
        if idle:
            summary = (
                "Historical Context is ready but has not been evaluated in this "
                "GUI session yet."
            )
        else:
            summary = state.message or f"Historical Context runtime is {state.phase.value}."
        return SubsystemHealth(
            name="context",
            role=SubsystemRole.CONTEXT,
            availability=availability,
            operational_health=health,
            evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
            summary=summary,
            details=tuple(details),
        )

    def _execute(self, request: ContextPresentationRequest) -> ContextViewState:
        with self._measure("context.background"):
            return self._presenter.evaluate_request(request)

    def _measure(self, operation: str) -> AbstractContextManager[None]:
        metrics = self._metrics
        return metrics.measure(operation) if metrics is not None else nullcontext()
