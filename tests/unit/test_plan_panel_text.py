from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

import pytest

pytest.importorskip("PySide6")

from codexbar.application.plan import evaluate_window_plan  # noqa: E402
from codexbar.domain.models import Fraction, UsageWindow, UsageWindowId  # noqa: E402
from codexbar.domain.quantities import TimeToReset  # noqa: E402
from codexbar.domain.settings import (  # noqa: E402
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)
from codexbar.ui.control_panel import (  # noqa: E402
    _duration_text,
    _plan_body_text,
    _plan_window_lines,
)

NOW = datetime(2026, 8, 14, 12, tzinfo=UTC)
WINDOW_ID = UsageWindowId("opaque-weekly")


def f(value: str) -> Fraction:
    return Fraction(Decimal(value))


def assessment(
    remaining: str,
    *,
    reserve: str | None = None,
    checkpoints: tuple[tuple[int, str], ...] = (),
    reset_hours: int | None = None,
):
    reserve_policy = UsageReservePolicy(
        () if reserve is None else (UsageReserve(WINDOW_ID, f(reserve)),)
    )
    checkpoint_policy = UsagePlanCheckpointPolicy(
        tuple(
            UsagePlanCheckpoint(
                WINDOW_ID,
                TimeToReset(timedelta(hours=hours)),
                f(minimum),
            )
            for hours, minimum in checkpoints
        )
    )
    resets_at = None if reset_hours is None else NOW + timedelta(hours=reset_hours)
    return evaluate_window_plan(
        window=UsageWindow(WINDOW_ID, "Weekly", f(remaining), resets_at=resets_at),
        observed_at=NOW,
        reserve_policy=reserve_policy,
        checkpoint_policy=checkpoint_policy,
    )


def test_active_checkpoint_renders_floor_source_signed_margin_and_compliance() -> None:
    lines = _plan_window_lines(
        "Weekly",
        assessment(
            "0.63",
            reserve="0.15",
            checkpoints=((72, "0.55"),),
            reset_hours=60,
        ),
    )

    assert lines == (
        "Weekly",
        "  Current: 63%",
        "  Active checkpoint: 72h -> minimum 55%",
        "  Effective floor: 55% (checkpoint)",
        "  Margin: +8 pp",
        "  Status: On plan",
    )


def test_checkpoint_duration_text_keeps_subweek_hours_and_compacts_long_days() -> None:
    assert _duration_text(timedelta(hours=72)) == "72h"
    assert _duration_text(timedelta(days=30)) == "30d"


def test_not_configured_and_no_active_checkpoint_are_explicit() -> None:
    not_configured = _plan_window_lines("Weekly", assessment("0.63"))
    no_active = _plan_window_lines(
        "Weekly",
        assessment(
            "0.63",
            checkpoints=((72, "0.55"),),
            reset_hours=100,
        ),
    )

    assert "  Plan policy: Not configured" in not_configured
    assert "  Status: Not applicable" in not_configured
    assert "  Checkpoint: No active checkpoint at current time-to-reset" in no_active


def test_missing_and_invalid_reset_are_explicit_without_checkpoint_claim() -> None:
    missing = _plan_window_lines(
        "Weekly",
        assessment("0.40", reserve="0.15", checkpoints=((72, "0.55"),)),
    )
    invalid = _plan_window_lines(
        "Weekly",
        assessment(
            "0.40",
            reserve="0.15",
            checkpoints=((72, "0.55"),),
            reset_hours=-1,
        ),
    )

    assert "  Checkpoint: Reset unavailable" in missing
    assert "  Effective floor: 15% (reserve)" in missing
    assert "  Checkpoint: Reset invalid or already passed" in invalid


def test_equal_reserve_and_checkpoint_show_both_sources() -> None:
    lines = _plan_window_lines(
        "Weekly",
        assessment(
            "0.55",
            reserve="0.55",
            checkpoints=((72, "0.55"),),
            reset_hours=60,
        ),
    )

    assert "  Effective floor: 55% (reserve + checkpoint)" in lines
    assert "  Margin: 0 pp" in lines
    assert "  Status: At plan floor" in lines


def test_stale_body_never_shows_current_plan_compliance_claim() -> None:
    state = cast(
        Any,
        SimpleNamespace(
            usage=SimpleNamespace(stale=True),
            plan=SimpleNamespace(available=False, windows=()),
        ),
    )

    text = _plan_body_text(state)

    assert text == "Plan unavailable while current usage is stale."
    assert "On plan" not in text
    assert "Below plan" not in text
