from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.ui.viewmodel import UsageViewModel


def test_current_view_state_preserves_stable_window_identity() -> None:
    window_id = UsageWindowId("window_300m")
    snapshot = UsageSnapshot(
        (
            UsageWindow(
                window_id,
                "5 hours",
                Fraction(Decimal("0.639")),
            ),
        ),
        datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
        UsageSource.MOCK,
    )

    state = UsageViewModel.from_snapshot(snapshot)

    assert state.windows[0].window_id == window_id


def test_current_presentation_preserves_whole_percent_semantics() -> None:
    snapshot = UsageSnapshot(
        (
            UsageWindow(
                UsageWindowId("window_300m"),
                "5 hours",
                Fraction(Decimal("0.639")),
            ),
        ),
        datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
        UsageSource.MOCK,
    )

    state = UsageViewModel.from_snapshot(snapshot)

    assert state.windows[0].percent_left == 63
    assert state.glance_text == "5h: 63%"


def test_same_label_does_not_replace_stable_identity() -> None:
    snapshot = UsageSnapshot(
        (
            UsageWindow(
                UsageWindowId("window_a"),
                "Weekly",
                Fraction(Decimal("0.80")),
            ),
            UsageWindow(
                UsageWindowId("window_b"),
                "Weekly",
                Fraction(Decimal("0.70")),
            ),
        ),
        datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
        UsageSource.MOCK,
    )

    state = UsageViewModel.from_snapshot(snapshot)

    assert [window.window_id.value for window in state.windows] == [
        "window_a",
        "window_b",
    ]
