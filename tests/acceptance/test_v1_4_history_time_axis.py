from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from codexbar.application.analytics import AnalysisPeriod
from codexbar.ui.history_dialog import _time_fraction, _time_ticks

START = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def test_24h_axis_spans_requested_interval_not_sample_extent() -> None:
    end = START + timedelta(hours=24)
    ticks = _time_ticks(START, end, AnalysisPeriod.HOURS_24)

    assert ticks[0][0] == START
    assert ticks[-1][0] == end
    assert len(ticks) == 5
    assert ticks[-1][1].startswith("now\n")


def test_7d_and_30d_axes_use_date_labels() -> None:
    seven_end = START + timedelta(days=7)
    thirty_end = START + timedelta(days=30)

    seven = _time_ticks(START, seven_end, AnalysisPeriod.DAYS_7)
    thirty = _time_ticks(START, thirty_end, AnalysisPeriod.DAYS_30)

    assert all(":" not in label for _, label in seven[:-1])
    assert all(":" not in label for _, label in thirty[:-1])
    assert seven[-1][1].startswith("now\n")
    assert thirty[-1][1].startswith("now\n")


def test_observation_position_is_relative_to_requested_domain() -> None:
    end = START + timedelta(hours=24)
    quarter = START + timedelta(hours=6)
    midpoint = START + timedelta(hours=12)

    assert _time_fraction(START, START, end) == 0.0
    assert _time_fraction(quarter, START, end) == 0.25
    assert _time_fraction(midpoint, START, end) == 0.5
    assert _time_fraction(end, START, end) == 1.0


def test_time_fraction_clamps_outside_requested_interval() -> None:
    end = START + timedelta(hours=24)

    assert _time_fraction(START - timedelta(hours=1), START, end) == 0.0
    assert _time_fraction(end + timedelta(hours=1), START, end) == 1.0
