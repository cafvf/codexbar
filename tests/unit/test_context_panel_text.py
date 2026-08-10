from __future__ import annotations

from decimal import Decimal

from codexbar.domain.models import UsageWindowId
from codexbar.ui.context_panel import _render_window
from codexbar.ui.context_viewmodel import ContextViewKind, ContextWindowViewState

WINDOW = UsageWindowId("opaque")


def state(kind: ContextViewKind, **kwargs) -> ContextWindowViewState:
    return ContextWindowViewState(
        window_id=WINDOW,
        label="Provider window",
        kind=kind,
        comparable_cycle_count=kwargs.pop("comparable_cycle_count", 5),
        status_text=kwargs.pop("status_text", "Limited empirical coverage."),
        **kwargs,
    )


def test_task_652_unavailable_always_renders_comparable_cycle_field() -> None:
    text = _render_window(
        state(
            ContextViewKind.UNAVAILABLE,
            comparable_cycle_count=None,
            status_text="Historical context is temporarily unavailable.",
        )
    )

    assert "Historical context is temporarily unavailable." in text
    assert "Comparable cycles: unavailable" in text


def test_task_653_sparse_renders_observed_range_not_median_or_middle_50() -> None:
    text = _render_window(
        state(
            ContextViewKind.SPARSE,
            comparable_cycle_count=3,
            status_text="Sparse empirical coverage.",
            range_low=Decimal("0.20"),
            range_high=Decimal("0.50"),
        )
    )

    assert "Comparable cycles: 3" in text
    assert "Observed historical range: 20%–50%" in text
    assert "Historical median" not in text
    assert "middle 50%" not in text.lower()


def test_task_654_limited_renders_median_range_and_rank() -> None:
    text = _render_window(
        state(
            ContextViewKind.LIMITED,
            median=Decimal("0.40"),
            range_low=Decimal("0.20"),
            range_high=Decimal("0.60"),
            rank_text="Historical comparison: 3 greater, 0 equal, 2 lower.",
        )
    )

    assert "Historical median: 40%" in text
    assert "Observed historical range: 20%–60%" in text
    assert "3 greater, 0 equal, 2 lower" in text


def test_task_655_established_renders_empirical_middle_50_and_rank() -> None:
    text = _render_window(
        state(
            ContextViewKind.ESTABLISHED,
            comparable_cycle_count=10,
            status_text="Established empirical coverage.",
            median=Decimal("0.55"),
            band_low=Decimal("0.325"),
            band_high=Decimal("0.775"),
            rank_text="Historical comparison: 4 greater, 1 equal, 5 lower.",
        )
    )

    assert "Comparable cycles: 10" in text
    assert "Historical median: 55%" in text
    assert "Empirical middle 50%: 32.5%–77.5%" in text
    assert "4 greater, 1 equal, 5 lower" in text
