from datetime import UTC, datetime
from decimal import Decimal

from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.ui.viewmodel import UsageViewModel


def _window(window_id: str, label: str, percent_left: str) -> UsageWindow:
    return UsageWindow(
        id=UsageWindowId(window_id),
        label=label,
        remaining=Fraction.from_percent(Decimal(percent_left)),
    )


def _snapshot(*windows: UsageWindow) -> UsageSnapshot:
    return UsageSnapshot(
        windows=windows,
        observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        source=UsageSource.MOCK,
    )


def test_ac_ui_010_five_hour_window_has_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_300m", "5 hours", "73")))

    assert state.windows[0].short_label == "5h"
    assert state.glance_text == "5h: 73%"


def test_ac_ui_011_weekly_window_has_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_10080m", "Weekly", "41")))

    assert state.windows[0].short_label == "W"
    assert state.glance_text == "W: 41%"


def test_ac_ui_012_two_known_windows_are_shown_together() -> None:
    state = UsageViewModel.from_snapshot(
        _snapshot(
            _window("window_300m", "5 hours", "73"),
            _window("window_10080m", "Weekly", "41"),
        )
    )

    assert state.glance_text == "5h: 73% · W: 41%"


def test_ac_ui_013_missing_window_is_omitted_not_fabricated() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_10080m", "Weekly", "41")))

    assert "5h" not in state.glance_text
    assert state.glance_text == "W: 41%"


def test_unknown_duration_gets_deterministic_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_1440m", "1 days", "90")))

    assert state.glance_text == "1d: 90%"
