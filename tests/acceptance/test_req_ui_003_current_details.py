from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton

from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsagePolicy,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
    UsageWindowState,
)
from codexbar.ui.controller import TrayPhase, TrayViewState
from codexbar.ui.current_panel import RichUsagePanel
from codexbar.ui.viewmodel import UsageViewModel

NOW = datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)


def app() -> QApplication:
    instance = QApplication.instance()
    return instance if isinstance(instance, QApplication) else QApplication([])


def snapshot(
    *windows: UsageWindow,
    freshness: Freshness = Freshness.CURRENT,
    observed_at: datetime = NOW,
) -> UsageSnapshot:
    return UsageSnapshot(
        tuple(windows),
        observed_at,
        UsageSource.MOCK,
        freshness,
    )


def current_state(
    usage_snapshot: UsageSnapshot,
    *,
    policy: UsagePolicy | None = None,
) -> TrayViewState:
    usage = (
        UsageViewModel.from_snapshot(usage_snapshot)
        if policy is None
        else UsageViewModel.from_snapshot(usage_snapshot, policy)
    )
    phase = TrayPhase.STALE if usage.stale else TrayPhase.FRESH
    return TrayViewState(phase=phase, usage=usage)


def labels(panel: RichUsagePanel) -> list[str]:
    return [label.text() for label in panel.findChildren(QLabel)]


def test_multiple_current_windows_render_without_fabrication() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.63")),
            ),
            UsageWindow(
                UsageWindowId("window_10080m"),
                "Weekly",
                Fraction(Decimal("0.81")),
            ),
        )
    )

    panel.render_state(state)

    text = labels(panel)
    assert any("5 hours" in item for item in text)
    assert any("63% left" in item for item in text)
    assert any("Weekly" in item for item in text)
    assert any("81% left" in item for item in text)
    assert len(panel.findChildren(QProgressBar)) == 2


def test_visual_indicator_matches_whole_percent_presentation() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.639")),
            )
        )
    )

    panel.render_state(state)

    bars = panel.findChildren(QProgressBar)
    assert len(bars) == 1
    assert bars[0].value() == 63
    assert bars[0].format() == "63%"


@pytest.mark.parametrize(
    ("remaining", "expected"),
    [
        ("0.50", UsageWindowState.AVAILABLE),
        ("0.20", UsageWindowState.LOW),
        ("0.00", UsageWindowState.EXHAUSTED),
    ],
)
def test_current_state_classification_uses_runtime_policy(
    remaining: str,
    expected: UsageWindowState,
) -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal(remaining)),
            )
        )
    )

    panel.render_state(state)

    assert any(expected.value.upper() in item for item in labels(panel))


def test_stale_current_snapshot_is_explicit_and_keeps_values() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.44")),
            ),
            freshness=Freshness.STALE,
        )
    )

    panel.render_state(state)

    text = labels(panel)
    assert any("STALE" in item for item in text)
    assert any("44% left" in item for item in text)


def test_observation_age_comes_from_snapshot_timestamp() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.50")),
            ),
            observed_at=NOW - timedelta(minutes=5, seconds=30),
        )
    )

    panel.render_state(state)

    assert any("5m 30s ago" in item for item in labels(panel))


def test_future_reset_shows_absolute_and_relative_time() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    reset_at = NOW + timedelta(hours=2, minutes=15)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.50")),
                resets_at=reset_at,
            )
        )
    )

    panel.render_state(state)

    assert any("in 2h 15m" in item for item in labels(panel))


def test_absent_reset_is_not_fabricated() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)
    state = current_state(
        snapshot(
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.50")),
            )
        )
    )

    panel.render_state(state)

    assert "Reset: not reported" in labels(panel)


def test_current_to_history_navigation_uses_stable_window_id() -> None:
    app()
    selected: list[UsageWindowId] = []
    panel = RichUsagePanel(
        on_history=selected.append,
        clock=lambda: NOW,
    )
    window_id = UsageWindowId("window_300m")
    state = current_state(
        snapshot(
            UsageWindow(
                window_id,
                "5 hours",
                Fraction(Decimal("0.50")),
            )
        )
    )
    panel.render_state(state)

    history_buttons = [
        button
        for button in panel.findChildren(QPushButton)
        if button.text() == "View history"
    ]
    assert len(history_buttons) == 1

    history_buttons[0].click()

    assert selected == [window_id]


def test_initial_hard_error_does_not_fabricate_current_cards() -> None:
    app()
    panel = RichUsagePanel(clock=lambda: NOW)

    panel.render_state(
        TrayViewState(
            phase=TrayPhase.ERROR,
            usage=None,
            message="provider unavailable",
        )
    )

    assert panel.findChildren(QProgressBar) == []
    assert any("provider unavailable" in item for item in labels(panel))
