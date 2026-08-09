from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Protocol

from codexbar.application.alerts import AlertService
from codexbar.application.refresh import RefreshCoordinator
from codexbar.domain.errors import CodexBarError
from codexbar.domain.models import DEFAULT_USAGE_POLICY, UsagePolicy, UsageSnapshot
from codexbar.domain.settings import AppSettings
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


class IntervalTimer(Protocol):
    def setInterval(self, milliseconds: int) -> None: ...


def apply_refresh_interval(timer: IntervalTimer, settings: AppSettings) -> None:
    timer.setInterval(settings.refresh_interval_seconds.value * 1000)


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
        usage_policy: UsagePolicy = DEFAULT_USAGE_POLICY,
        alert_service: AlertService | None = None,
        notifications_enabled: bool = True,
    ) -> None:
        self._coordinator = coordinator
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="codexbar"
        )
        self._owns_executor = executor is None
        self._usage_policy = usage_policy
        self._alert_service = alert_service
        self._notifications_enabled = notifications_enabled
        self._future: Future[UsageSnapshot] | None = None
        self._state = TrayViewState(phase=TrayPhase.LOADING)

    @property
    def state(self) -> TrayViewState:
        return self._state

    @property
    def busy(self) -> bool:
        return self._future is not None and not self._future.done()

    def apply_usage_policy(self, policy: UsagePolicy) -> None:
        self._usage_policy = policy

    def apply_notifications_enabled(self, enabled: bool) -> None:
        self._notifications_enabled = enabled

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

        if self._alert_service is not None:
            self._alert_service.process(
                snapshot,
                self._usage_policy,
                notifications_enabled=self._notifications_enabled,
            )

        usage = UsageViewModel.from_snapshot(snapshot, self._usage_policy)
        phase = TrayPhase.STALE if usage.stale else TrayPhase.FRESH
        self._state = TrayViewState(phase=phase, usage=usage)
        return self._state

    def close(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
