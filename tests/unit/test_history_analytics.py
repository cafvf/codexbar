from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisService,
    HistoricalAnalysisState,
)
from codexbar.application.history import HistoricalWindowObservation, HistoricalWindowSample
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId

T1 = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("weekly")


def sample(offset_hours: int, remaining: str) -> HistoricalWindowSample:
    return HistoricalWindowSample(
        observed_at=T1 + timedelta(hours=offset_hours),
        source=UsageSource.MOCK,
        observation=HistoricalWindowObservation(
            window_id=WINDOW,
            label="Weekly",
            remaining=Fraction(Decimal(remaining)),
        ),
    )


class FakeRepo:
    def __init__(self, samples: tuple[HistoricalWindowSample, ...]) -> None:
        self.samples = samples

    def query_window(self, window_id: UsageWindowId, interval):
        return tuple(
            item
            for item in self.samples
            if item.observation.window_id == window_id and interval.contains(item.observed_at)
        )

    def list_window_ids(self, interval):
        return tuple(
            sorted(
                {
                    item.observation.window_id
                    for item in self.samples
                    if interval.contains(item.observed_at)
                },
                key=lambda item: item.value,
            )
        )


def test_mixed_sequence_summary_and_increase() -> None:
    samples = tuple(
        sample(i, value)
        for i, value in enumerate(("0.82", "0.63", "0.41", "1.00", "0.91"))
    )
    end = T1 + timedelta(hours=6)
    result = HistoricalAnalysisService(FakeRepo(samples)).analyze(
        WINDOW,
        AnalysisPeriod.HOURS_24,
        end=end,
    )

    assert result.state is HistoricalAnalysisState.READY
    assert result.summary is not None
    assert result.summary.observation_count == 5
    assert result.summary.first_remaining.value == Decimal("0.82")
    assert result.summary.latest_remaining.value == Decimal("0.91")
    assert result.summary.observed_min.value == Decimal("0.41")
    assert result.summary.observed_max.value == Decimal("1.00")
    assert result.summary.observed_change is not None
    assert result.summary.observed_change.value == Decimal("0.09")
    assert len(result.observed_increases) == 1
    assert result.observed_increases[0].previous.observation.remaining.value == Decimal("0.41")
    assert result.observed_increases[0].current.observation.remaining.value == Decimal("1.00")


def test_singleton_has_no_observed_change() -> None:
    result = HistoricalAnalysisService(FakeRepo((sample(0, "0.42"),))).analyze(
        WINDOW,
        AnalysisPeriod.HOURS_24,
        end=T1 + timedelta(hours=1),
    )
    assert result.summary is not None
    assert result.summary.observed_change is None
    assert result.observed_increases == ()


def test_empty_is_explicit() -> None:
    result = HistoricalAnalysisService(FakeRepo(())).analyze(
        WINDOW,
        AnalysisPeriod.HOURS_24,
        end=T1 + timedelta(hours=1),
    )
    assert result.state is HistoricalAnalysisState.EMPTY
    assert result.summary is None
    assert result.samples == ()


def test_period_mapping_uses_one_end_instant() -> None:
    service = HistoricalAnalysisService(FakeRepo(()))
    end = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
    interval = service.interval_for(AnalysisPeriod.DAYS_7, end=end)
    assert interval.end == end
    assert interval.start == end - timedelta(days=7)


def test_analysis_rejects_naive_end() -> None:
    service = HistoricalAnalysisService(FakeRepo(()))
    with pytest.raises(ValueError, match="timezone-aware"):
        service.interval_for(AnalysisPeriod.HOURS_24, end=T1.replace(tzinfo=None))
