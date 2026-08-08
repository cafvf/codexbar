from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from codexbar.application.refresh import RefreshCoordinator
from codexbar.domain.errors import CodexBarError
from codexbar.domain.models import UsageSnapshot
from codexbar.ui.viewmodel import UsageViewModel, UsageViewState


class TrayPhase(StrEnum):
    LOADING = "loading"
    FRESH = "fresh"
    STALE = "stale"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TraySettings:
    refresh_interval_seconds: int = 60
    poll_interval_milliseconds: int = 100

    def __post_init__(self) -> None:
        if self.refresh_interval_seconds <= 0:
            raise ValueError("refresh_interval_seconds must be positive")
        if self.poll_interval_milliseconds <= 0:
            raise ValueError("poll_interval_milliseconds must be positive")


DEFAULT_TRAY_SETTINGS: Final = TraySettings()


@dataclass(frozen=True, slots=True)
class TrayViewState:
    phase: TrayPhase
    usage: UsageViewState | None = None
    message: str | None = None


class TrayController:
    """Framework-independent controller for asynchronous tray refreshes."""

    def __init__(
        self,
        coordinator: RefreshCoordinator,
        executor: Executor | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="codexbar")
        self._owns_executor = executor is None
        self._future: Future[UsageSnapshot] | None = None
        self._state = TrayViewState(phase=TrayPhase.LOADING)

    @property
    def state(self) -> TrayViewState:
        return self._state

    @property
    def busy(self) -> bool:
        return self._future is not None and not self._future.done()

    def start_refresh(self) -> bool:
        if self.busy:
            return False
        self._state = TrayViewState(
            phase=TrayPhase.LOADING,
            usage=self._state.usage,
            message=None,
        )
        self._future = self._executor.submit(self._coordinator.refresh)
        return True

    def poll(self) -> TrayViewState:
        future = self._future
        if future is None or not future.done():
            return self._state

        self._future = None
        try:
            snapshot = future.result()
        except CodexBarError as exc:
            self._state = TrayViewState(
                phase=TrayPhase.ERROR,
                usage=self._state.usage,
                message=str(exc),
            )
            return self._state

        usage = UsageViewModel.from_snapshot(snapshot)
        phase = TrayPhase.STALE if usage.stale else TrayPhase.FRESH
        self._state = TrayViewState(phase=phase, usage=usage)
        return self._state

    def close(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
