from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisResult,
    HistoricalAnalysisState,
    HistoricalWindowDiscovery,
)
from codexbar.domain.models import UsageWindowId


class HistoryViewPhase(StrEnum):
    LOADING = "loading"
    READY = "ready"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class HistoryChartPoint:
    observed_at: datetime
    percent_left: Decimal
    label: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("chart point timestamp must be timezone-aware")
        if not self.percent_left.is_finite():
            raise ValueError("chart point percentage must be finite")
        if not Decimal("0") <= self.percent_left <= Decimal("100"):
            raise ValueError("chart point percentage must be between 0 and 100")
        if not self.label.strip():
            raise ValueError("chart point label must not be blank")


@dataclass(frozen=True, slots=True)
class HistorySummaryViewState:
    observation_count: int
    first_observed_at: datetime
    latest_observed_at: datetime
    first_percent_left: Decimal
    latest_percent_left: Decimal
    observed_min_percent_left: Decimal
    observed_max_percent_left: Decimal
    observed_change_percentage_points: Decimal | None


@dataclass(frozen=True, slots=True)
class HistoryViewState:
    phase: HistoryViewPhase
    period: AnalysisPeriod
    interval_start: datetime | None = None
    interval_end: datetime | None = None
    available_window_ids: tuple[UsageWindowId, ...] = ()
    selected_window_id: UsageWindowId | None = None
    selected_label: str | None = None
    summary: HistorySummaryViewState | None = None
    chart_points: tuple[HistoryChartPoint, ...] = ()
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.phase is HistoryViewPhase.READY:
            if (
                self.interval_start is None
                or self.interval_end is None
                or self.selected_window_id is None
                or self.selected_label is None
                or self.summary is None
                or not self.chart_points
            ):
                raise ValueError("ready history view requires selected analytical data")
        elif self.summary is not None or self.chart_points:
            raise ValueError("non-ready history view must not contain analytical data")


def loading_history_view(period: AnalysisPeriod) -> HistoryViewState:
    return HistoryViewState(phase=HistoryViewPhase.LOADING, period=period)


def history_view_from_results(
    discovery: HistoricalWindowDiscovery,
    analysis: HistoricalAnalysisResult | None,
    *,
    selected_window_id: UsageWindowId | None,
) -> HistoryViewState:
    phase = _map_phase(discovery.state)
    if discovery.state is not HistoricalAnalysisState.READY:
        return HistoryViewState(
            phase=phase,
            period=_period_from_interval(discovery),
            interval_start=discovery.interval.start,
            interval_end=discovery.interval.end,
            diagnostic=discovery.diagnostic,
        )

    period = _period_from_interval(discovery)
    if analysis is None:
        return HistoryViewState(
            phase=HistoryViewPhase.EMPTY,
            period=period,
            interval_start=discovery.interval.start,
            interval_end=discovery.interval.end,
            available_window_ids=discovery.window_ids,
            selected_window_id=selected_window_id,
        )

    analysis_phase = _map_phase(analysis.state)
    if analysis.state is not HistoricalAnalysisState.READY:
        return HistoryViewState(
            phase=analysis_phase,
            period=period,
            interval_start=discovery.interval.start,
            interval_end=discovery.interval.end,
            available_window_ids=discovery.window_ids,
            selected_window_id=selected_window_id,
            diagnostic=analysis.diagnostic,
        )

    if analysis.summary is None or not analysis.samples:
        raise ValueError("ready analysis must contain summary and samples")

    latest_label = analysis.samples[-1].observation.label
    summary = analysis.summary
    return HistoryViewState(
        phase=HistoryViewPhase.READY,
        period=period,
        interval_start=discovery.interval.start,
        interval_end=discovery.interval.end,
        available_window_ids=discovery.window_ids,
        selected_window_id=analysis.window_id,
        selected_label=latest_label,
        summary=HistorySummaryViewState(
            observation_count=summary.observation_count,
            first_observed_at=summary.first_observed_at,
            latest_observed_at=summary.latest_observed_at,
            first_percent_left=summary.first_remaining.percent,
            latest_percent_left=summary.latest_remaining.percent,
            observed_min_percent_left=summary.observed_min.percent,
            observed_max_percent_left=summary.observed_max.percent,
            observed_change_percentage_points=(
                summary.observed_change.value * Decimal("100")
                if summary.observed_change is not None
                else None
            ),
        ),
        chart_points=tuple(
            HistoryChartPoint(
                observed_at=sample.observed_at,
                percent_left=sample.observation.remaining.percent,
                label=sample.observation.label,
            )
            for sample in analysis.samples
        ),
    )


def _map_phase(state: HistoricalAnalysisState) -> HistoryViewPhase:
    return HistoryViewPhase(state.value)


def _period_from_interval(discovery: HistoricalWindowDiscovery) -> AnalysisPeriod:
    duration = discovery.interval.end - discovery.interval.start
    for period in AnalysisPeriod:
        if duration == period.duration:
            return period
    raise ValueError("historical discovery interval does not map to a supported period")
