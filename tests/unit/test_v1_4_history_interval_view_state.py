from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.analytics import AnalysisPeriod, HistoricalAnalysisService
from codexbar.application.history import (
    HistoricalWindowObservation,
    HistoricalWindowSample,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.ui.history_viewmodel import history_view_from_results

START = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("window_300m")


class Repo:
    def query_window(self, window_id, interval):
        return (
            HistoricalWindowSample(
                observed_at=START + timedelta(hours=12),
                source=UsageSource.MOCK,
                observation=HistoricalWindowObservation(
                    window_id=WINDOW,
                    label="5 hours",
                    remaining=Fraction(Decimal("0.50")),
                ),
            ),
        )

    def list_window_ids(self, interval):
        return (WINDOW,)


def test_ready_history_view_preserves_requested_interval_domain() -> None:
    end = START + timedelta(hours=24)
    service = HistoricalAnalysisService(Repo())
    discovery = service.discover(AnalysisPeriod.HOURS_24, end=end)
    analysis = service.analyze(WINDOW, AnalysisPeriod.HOURS_24, end=end)

    state = history_view_from_results(
        discovery,
        analysis,
        selected_window_id=WINDOW,
    )

    assert state.interval_start == START
    assert state.interval_end == end
    assert state.period is AnalysisPeriod.HOURS_24
