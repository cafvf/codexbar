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
from codexbar.ui.current_panel import (
    _format_age,
    _format_reset_relative,
)
from codexbar.ui.viewmodel import UsageViewModel


def test_age_formatting_uses_observation_timestamp() -> None:
    now = datetime(2026, 8, 9, 12, 5, 30, tzinfo=UTC)
    observed = datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)

    assert _format_age(now, observed) == "5m 30s"


def test_future_reset_gets_relative_duration() -> None:
    now = datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)
    reset = datetime(2026, 8, 9, 14, 15, 0, tzinfo=UTC)

    assert _format_reset_relative(now, reset) == "in 2h 15m"


def test_past_reset_is_not_reinterpreted() -> None:
    now = datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)
    reset = datetime(2026, 8, 9, 11, 59, 0, tzinfo=UTC)

    assert _format_reset_relative(now, reset) == "reset time passed"


def test_current_card_contract_preserves_window_identity_and_percent() -> None:
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
    assert state.windows[0].percent_left == 63
