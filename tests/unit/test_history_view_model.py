from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisService,
    HistoricalAnalysisState,
)
from codexbar.application.history import (
    HistoricalWindowObservation,
    HistoricalWindowSample,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.ui.history_viewmodel import (
    HistoryChartPoint,
    HistoryViewPhase,
    history_view_from_results,
)

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("weekly")


def sample(hour: int, value: str, label: str = "Weekly") -> HistoricalWindowSample:
    return HistoricalWindowSample(
        observed_at=T0 + timedelta(hours=hour),
        source=UsageSource.MOCK,
        observation=HistoricalWindowObservation(
            window_id=WINDOW,
            label=label,
            remaining=Fraction(Decimal(value)),
        ),
    )


class Repo:
    def __init__(self, samples: tuple[HistoricalWindowSample, ...]) -> None:
        self.samples = samples

    def query_window(self, window_id, interval):
        return tuple(item for item in self.samples if interval.contains(item.observed_at))

    def list_window_ids(self, interval):
        has_sample = any(
            interval.contains(item.observed_at) for item in self.samples
        )
        return (WINDOW,) if has_sample else ()


def ready_results(samples: tuple[HistoricalWindowSample, ...]):
    end = T0 + timedelta(hours=6)
    service = HistoricalAnalysisService(Repo(samples))
    discovery = service.discover(AnalysisPeriod.HOURS_24, end=end)
    analysis = service.analyze(WINDOW, AnalysisPeriod.HOURS_24, end=end)
    return discovery, analysis


def test_ready_view_preserves_exact_observation_points() -> None:
    samples = (
        sample(0, "0.82", "Weekly old"),
        sample(1, "0.41", "Weekly middle"),
        sample(2, "1.00", "Weekly new"),
    )
    discovery, analysis = ready_results(samples)

    state = history_view_from_results(
        discovery,
        analysis,
        selected_window_id=WINDOW,
    )

    assert state.phase is HistoryViewPhase.READY
    assert state.selected_window_id == WINDOW
    assert state.selected_label == "Weekly new"
    assert [point.observed_at for point in state.chart_points] == [
        item.observed_at for item in samples
    ]
    assert [point.percent_left for point in state.chart_points] == [
        Decimal("82"),
        Decimal("41"),
        Decimal("100"),
    ]
    assert [point.label for point in state.chart_points] == [
        "Weekly old",
        "Weekly middle",
        "Weekly new",
    ]


def test_summary_maps_analytical_values_without_recalculation() -> None:
    discovery, analysis = ready_results(
        (sample(0, "0.82"), sample(1, "0.63"), sample(2, "0.91"))
    )
    state = history_view_from_results(discovery, analysis, selected_window_id=WINDOW)

    assert state.summary is not None
    assert state.summary.observation_count == 3
    assert state.summary.first_percent_left == Decimal("82")
    assert state.summary.latest_percent_left == Decimal("91")
    assert state.summary.observed_min_percent_left == Decimal("63")
    assert state.summary.observed_max_percent_left == Decimal("91")
    assert state.summary.observed_change_percentage_points == Decimal("9")


def test_singleton_change_remains_unavailable() -> None:
    discovery, analysis = ready_results((sample(0, "0.42"),))
    state = history_view_from_results(discovery, analysis, selected_window_id=WINDOW)

    assert state.summary is not None
    assert state.summary.observed_change_percentage_points is None


def test_empty_discovery_maps_to_empty_view() -> None:
    end = T0 + timedelta(hours=1)
    service = HistoricalAnalysisService(Repo(()))
    discovery = service.discover(AnalysisPeriod.HOURS_24, end=end)

    state = history_view_from_results(
        discovery,
        None,
        selected_window_id=None,
    )

    assert discovery.state is HistoricalAnalysisState.EMPTY
    assert state.phase is HistoryViewPhase.EMPTY
    assert state.chart_points == ()
    assert state.summary is None


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (Decimal("-1"), "between 0 and 100"),
        (Decimal("101"), "between 0 and 100"),
        (Decimal("NaN"), "finite"),
    ],
)
def test_chart_point_rejects_invalid_percentage(value: Decimal, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        HistoryChartPoint(T0, value, "Weekly")
