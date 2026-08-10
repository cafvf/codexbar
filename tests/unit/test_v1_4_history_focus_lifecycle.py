from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from codexbar.application.analytics import AnalysisPeriod, HistoricalAnalysisState
from codexbar.domain.models import UsageWindowId
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_viewmodel import HistoryViewPhase

FOCUSED = UsageWindowId("window_300m")
OTHER = UsageWindowId("window_10080m")
NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


class Service:
    def discover(self, period, *, end):
        return SimpleNamespace(
            state=HistoricalAnalysisState.READY,
            interval=SimpleNamespace(start=end - period.duration, end=end),
            window_ids=(OTHER,),
            diagnostic=None,
        )

    def analyze(self, window_id, period, *, end):
        assert window_id == FOCUSED
        return SimpleNamespace(
            state=HistoricalAnalysisState.EMPTY,
            interval=SimpleNamespace(start=end - period.duration, end=end),
            window_id=window_id,
            samples=(),
            summary=None,
            observed_increases=(),
            diagnostic=None,
        )


def test_explicit_history_focus_does_not_fallback_to_another_window() -> None:
    controller = HistoryController(Service(), clock=lambda: NOW)
    controller.start(AnalysisPeriod.HOURS_24, window_id=FOCUSED)
    while controller.busy:
        pass

    state = controller.poll()

    assert state.phase is HistoryViewPhase.EMPTY
    assert state.selected_window_id == FOCUSED
    controller.close()
