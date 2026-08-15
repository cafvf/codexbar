from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from codexbar.application.history import (
    HistoricalWindowSample,
    HistoryError,
    HistoryInterval,
    HistorySchemaError,
)
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.quantities import FractionDelta


class AnalysisPeriod(StrEnum):
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"

    @property
    def duration(self) -> timedelta:
        if self is AnalysisPeriod.HOURS_24:
            return timedelta(hours=24)
        if self is AnalysisPeriod.DAYS_7:
            return timedelta(days=7)
        return timedelta(days=30)


class HistoricalAnalysisState(StrEnum):
    READY = "ready"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ObservedIncrease:
    previous: HistoricalWindowSample
    current: HistoricalWindowSample

    def __post_init__(self) -> None:
        if self.current.observed_at < self.previous.observed_at:
            raise ValueError("observed increase samples must be chronological")
        if (
            self.current.observation.remaining.value
            <= self.previous.observation.remaining.value
        ):
            raise ValueError("observed increase requires a positive remaining change")


@dataclass(frozen=True, slots=True)
class HistoricalSummary:
    observation_count: int
    first_observed_at: datetime
    latest_observed_at: datetime
    first_remaining: Fraction
    latest_remaining: Fraction
    observed_min: Fraction
    observed_max: Fraction
    observed_change: FractionDelta | None

    def __post_init__(self) -> None:
        if self.observation_count <= 0:
            raise ValueError("historical summary requires at least one observation")
        if self.latest_observed_at < self.first_observed_at:
            raise ValueError("latest observation must not precede first observation")


@dataclass(frozen=True, slots=True)
class HistoricalAnalysisResult:
    state: HistoricalAnalysisState
    window_id: UsageWindowId
    interval: HistoryInterval
    samples: tuple[HistoricalWindowSample, ...] = ()
    summary: HistoricalSummary | None = None
    observed_increases: tuple[ObservedIncrease, ...] = ()
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.state is HistoricalAnalysisState.READY:
            if not self.samples or self.summary is None:
                raise ValueError("ready analysis requires samples and summary")
        elif self.samples or self.summary is not None or self.observed_increases:
            raise ValueError("non-ready analysis must not contain analytical data")


@dataclass(frozen=True, slots=True)
class HistoricalWindowDiscovery:
    state: HistoricalAnalysisState
    interval: HistoryInterval
    window_ids: tuple[UsageWindowId, ...] = ()
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.state is HistoricalAnalysisState.READY and not self.window_ids:
            raise ValueError("ready discovery requires at least one window")
        if self.state is not HistoricalAnalysisState.READY and self.window_ids:
            raise ValueError("non-ready discovery must not contain windows")


class HistoryAnalyticsRepository(Protocol):
    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]: ...

    def list_window_ids(
        self,
        interval: HistoryInterval,
    ) -> tuple[UsageWindowId, ...]: ...


class AbsentHistoryAnalyticsRepository:
    """Read-only repository representing history storage that does not exist."""

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]:
        return ()

    def list_window_ids(
        self,
        interval: HistoryInterval,
    ) -> tuple[UsageWindowId, ...]:
        return ()


class FailedHistoryAnalyticsRepository:
    """Read-only repository that preserves a normalized open-time history failure."""

    def __init__(self, error: HistoryError) -> None:
        self._error = error

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]:
        raise self._error

    def list_window_ids(
        self,
        interval: HistoryInterval,
    ) -> tuple[UsageWindowId, ...]:
        raise self._error


class HistoricalAnalysisService:
    def __init__(
        self,
        repository: HistoryAnalyticsRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def interval_for(
        self,
        period: AnalysisPeriod,
        *,
        end: datetime | None = None,
    ) -> HistoryInterval:
        resolved_end = end if end is not None else self._clock()
        if resolved_end.tzinfo is None or resolved_end.utcoffset() is None:
            raise ValueError("analysis end must be timezone-aware")
        resolved_end = resolved_end.astimezone(UTC)
        return HistoryInterval(resolved_end - period.duration, resolved_end)

    def discover(
        self,
        period: AnalysisPeriod,
        *,
        end: datetime | None = None,
    ) -> HistoricalWindowDiscovery:
        interval = self.interval_for(period, end=end)
        try:
            window_ids = self._repository.list_window_ids(interval)
        except HistorySchemaError as exc:
            return HistoricalWindowDiscovery(
                state=HistoricalAnalysisState.UNSUPPORTED,
                interval=interval,
                diagnostic=str(exc),
            )
        except HistoryError as exc:
            return HistoricalWindowDiscovery(
                state=HistoricalAnalysisState.UNAVAILABLE,
                interval=interval,
                diagnostic=str(exc),
            )
        if not window_ids:
            return HistoricalWindowDiscovery(
                state=HistoricalAnalysisState.EMPTY,
                interval=interval,
            )
        return HistoricalWindowDiscovery(
            state=HistoricalAnalysisState.READY,
            interval=interval,
            window_ids=window_ids,
        )

    def analyze(
        self,
        window_id: UsageWindowId,
        period: AnalysisPeriod,
        *,
        end: datetime | None = None,
    ) -> HistoricalAnalysisResult:
        interval = self.interval_for(period, end=end)
        try:
            samples = self._repository.query_window(window_id, interval)
        except HistorySchemaError as exc:
            return self._failure(
                HistoricalAnalysisState.UNSUPPORTED,
                window_id,
                interval,
                exc,
            )
        except HistoryError as exc:
            return self._failure(
                HistoricalAnalysisState.UNAVAILABLE,
                window_id,
                interval,
                exc,
            )
        if not samples:
            return HistoricalAnalysisResult(
                state=HistoricalAnalysisState.EMPTY,
                window_id=window_id,
                interval=interval,
            )
        ordered = tuple(sorted(samples, key=lambda item: item.observed_at))
        return HistoricalAnalysisResult(
            state=HistoricalAnalysisState.READY,
            window_id=window_id,
            interval=interval,
            samples=ordered,
            summary=_summarize(ordered),
            observed_increases=_observed_increases(ordered),
        )

    @staticmethod
    def _failure(
        state: HistoricalAnalysisState,
        window_id: UsageWindowId,
        interval: HistoryInterval,
        exc: HistoryError,
    ) -> HistoricalAnalysisResult:
        return HistoricalAnalysisResult(
            state=state,
            window_id=window_id,
            interval=interval,
            diagnostic=str(exc),
        )


def _summarize(
    samples: tuple[HistoricalWindowSample, ...],
) -> HistoricalSummary:
    if not samples:
        raise ValueError("cannot summarize empty historical samples")
    first = samples[0]
    latest = samples[-1]
    remaining = tuple(sample.observation.remaining for sample in samples)
    change = None
    if len(samples) >= 2:
        change = FractionDelta(
            latest.observation.remaining.value
            - first.observation.remaining.value
        )
    return HistoricalSummary(
        observation_count=len(samples),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        first_remaining=first.observation.remaining,
        latest_remaining=latest.observation.remaining,
        observed_min=min(remaining, key=lambda item: item.value),
        observed_max=max(remaining, key=lambda item: item.value),
        observed_change=change,
    )


def _observed_increases(
    samples: tuple[HistoricalWindowSample, ...],
) -> tuple[ObservedIncrease, ...]:
    return tuple(
        ObservedIncrease(previous, current)
        for previous, current in zip(samples, samples[1:], strict=False)
        if current.observation.remaining.value > previous.observation.remaining.value
    )
