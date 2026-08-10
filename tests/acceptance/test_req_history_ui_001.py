from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisService,
)
from codexbar.application.history import (
    HistoricalWindowObservation,
    HistoricalWindowSample,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_dialog import HistoryDialog
from codexbar.ui.history_viewmodel import HistoryViewPhase

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
WEEKLY = UsageWindowId("weekly")
SHORT = UsageWindowId("window_300m")


class Repo:
    def __init__(self, samples: tuple[HistoricalWindowSample, ...]) -> None:
        self.samples = samples

    def query_window(self, window_id, interval):
        return tuple(
            sample
            for sample in self.samples
            if sample.observation.window_id == window_id
            and interval.contains(sample.observed_at)
        )

    def list_window_ids(self, interval):
        return tuple(
            sorted(
                {
                    sample.observation.window_id
                    for sample in self.samples
                    if interval.contains(sample.observed_at)
                },
                key=lambda value: value.value,
            )
        )


def sample(
    window_id: UsageWindowId,
    hour: int,
    remaining: str,
    label: str,
) -> HistoricalWindowSample:
    return HistoricalWindowSample(
        observed_at=T0 + timedelta(hours=hour),
        source=UsageSource.MOCK,
        observation=HistoricalWindowObservation(
            window_id=window_id,
            label=label,
            remaining=Fraction(Decimal(remaining)),
        ),
    )


def app() -> QApplication:
    instance = QApplication.instance()
    return instance if isinstance(instance, QApplication) else QApplication([])


def completed_dialog(samples: tuple[HistoricalWindowSample, ...]) -> HistoryDialog:
    controller = HistoryController(
        HistoricalAnalysisService(Repo(samples)),
        clock=lambda: T0 + timedelta(hours=6),
    )
    dialog = HistoryDialog(controller)
    dialog.open_history()
    while controller.busy:
        QApplication.processEvents()
    dialog.render_state(controller.poll())
    return dialog


def test_history_dialog_defaults_to_24h_and_selects_window() -> None:
    app()
    dialog = completed_dialog((sample(WEEKLY, 0, "0.80", "Weekly"),))

    assert dialog._last_state is not None
    assert dialog._last_state.phase is HistoryViewPhase.READY
    assert dialog._last_state.period is AnalysisPeriod.HOURS_24
    assert dialog._last_state.selected_window_id == WEEKLY
    assert dialog.period_combo.currentText() == "24h"

    dialog._controller.close()
    dialog.deleteLater()


def test_history_dialog_renders_discrete_observations_and_summary() -> None:
    app()
    dialog = completed_dialog(
        (
            sample(WEEKLY, 0, "0.82", "Weekly"),
            sample(WEEKLY, 1, "0.41", "Weekly"),
            sample(WEEKLY, 2, "1.00", "Weekly"),
        )
    )

    assert [point.percent_left for point in dialog.chart.points] == [
        Decimal("82"),
        Decimal("41"),
        Decimal("100"),
    ]
    assert dialog._summary_values["count"].text() == "3"
    assert dialog._summary_values["minimum"].text() == "41%"
    assert dialog._summary_values["maximum"].text() == "100%"
    assert dialog._summary_values["change"].text() == "18 pp"

    dialog._controller.close()
    dialog.deleteLater()


def test_history_dialog_empty_state_is_not_zero_percent_chart() -> None:
    app()
    dialog = completed_dialog(())

    assert dialog._last_state is not None
    assert dialog._last_state.phase is HistoryViewPhase.EMPTY
    assert dialog.chart.points == ()
    assert "No stored observations" in dialog.status_label.text()
    assert dialog._summary_values["latest_remaining"].text() == "—"

    dialog._controller.close()
    dialog.deleteLater()


def test_explicit_window_focus_is_preserved_internally() -> None:
    app()
    controller = HistoryController(
        HistoricalAnalysisService(
            Repo(
                (
                    sample(WEEKLY, 0, "0.80", "Weekly"),
                    sample(SHORT, 0, "0.90", "5 hours"),
                )
            )
        ),
        clock=lambda: T0 + timedelta(hours=6),
    )
    dialog = HistoryDialog(controller)

    dialog.open_history(window_id=SHORT)
    while controller.busy:
        QApplication.processEvents()
    dialog.render_state(controller.poll())

    assert dialog._last_state is not None
    assert dialog._last_state.selected_window_id == SHORT
    assert not hasattr(dialog, "window_combo")

    controller.close()
    dialog.deleteLater()
