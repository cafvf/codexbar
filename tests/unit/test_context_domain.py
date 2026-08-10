from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from codexbar.domain.context import (
    ContextObservation,
    ContextSelectionState,
    CycleIdentity,
    TimeToReset,
    contextual_tolerance,
    select_context_references,
)
from codexbar.domain.models import Fraction, UsageWindowId

W = UsageWindowId("opaque-window")
NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def observation(
    *,
    observed_at: datetime,
    resets_at: datetime | None,
    remaining: str = "0.50",
    window_id: UsageWindowId = W,
) -> ContextObservation:
    return ContextObservation(
        window_id=window_id,
        observed_at=observed_at,
        remaining=Fraction(Decimal(remaining)),
        resets_at=resets_at,
    )


def current_with_h(hours: float) -> ContextObservation:
    return observation(
        observed_at=NOW,
        resets_at=NOW + timedelta(hours=hours),
    )


def historical_at_h(
    *,
    observed_at: datetime,
    hours: float,
    remaining: str,
    reset_marker: datetime | None = None,
) -> ContextObservation:
    resets_at = reset_marker or observed_at + timedelta(hours=hours)
    return observation(
        observed_at=observed_at,
        resets_at=resets_at,
        remaining=remaining,
    )


def selected_remaining(
    current: ContextObservation,
    historical: tuple[ContextObservation, ...],
) -> list[Decimal]:
    result = select_context_references(current=current, historical=historical)
    assert result.state is ContextSelectionState.READY
    assert result.reference_set is not None
    return [item.remaining.value for item in result.reference_set.observations]


def test_task_620_time_to_reset_normalizes_equivalent_instants_to_utc() -> None:
    minus_three = timezone(timedelta(hours=-3))
    observed = datetime(2026, 8, 10, 9, 0, tzinfo=minus_three)
    reset = datetime(2026, 8, 10, 14, 0, tzinfo=UTC)

    value = TimeToReset.from_instants(observed_at=observed, resets_at=reset)

    assert value.duration == timedelta(hours=2)


def test_task_620_time_to_reset_rejects_naive_or_negative_values() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        TimeToReset.from_instants(
            observed_at=NOW.replace(tzinfo=None),
            resets_at=NOW + timedelta(hours=1),
        )

    with pytest.raises(ValueError, match="negative"):
        TimeToReset.from_instants(
            observed_at=NOW,
            resets_at=NOW - timedelta(microseconds=1),
        )


def test_task_621_cycle_identity_normalizes_reset_timezone() -> None:
    reset_utc = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    reset_minus_three = datetime(
        2026,
        8,
        11,
        9,
        0,
        tzinfo=timezone(timedelta(hours=-3)),
    )

    assert CycleIdentity(W, reset_utc) == CycleIdentity(W, reset_minus_three)


def test_task_622_missing_current_reset_is_explicit_absence() -> None:
    result = select_context_references(
        current=observation(observed_at=NOW, resets_at=None),
        historical=(),
    )

    assert result.state is ContextSelectionState.CURRENT_RESET_MISSING
    assert result.reference_set is None


def test_task_622_missing_or_invalid_historical_reset_is_excluded() -> None:
    current = current_with_h(10)
    invalid = observation(
        observed_at=NOW - timedelta(days=1),
        resets_at=NOW - timedelta(days=1, microseconds=1),
    )
    missing = observation(
        observed_at=NOW - timedelta(days=2),
        resets_at=None,
    )

    result = select_context_references(
        current=current,
        historical=(missing, invalid),
    )

    assert result.state is ContextSelectionState.NO_IDENTIFIABLE_CYCLES


def test_tv_1601_tolerance_cap_exact_boundary_and_epsilon() -> None:
    current = current_with_h(100)

    assert contextual_tolerance(
        TimeToReset.from_instants(
            observed_at=current.observed_at,
            resets_at=current.resets_at,  # type: ignore[arg-type]
        )
    ) == timedelta(hours=2)

    eligible_observed = NOW - timedelta(days=4)
    ineligible_observed = NOW - timedelta(days=8)
    eligible = historical_at_h(
        observed_at=eligible_observed,
        hours=102,
        remaining="0.60",
    )
    ineligible = historical_at_h(
        observed_at=ineligible_observed,
        hours=102,
        remaining="0.40",
        reset_marker=ineligible_observed
        + timedelta(hours=102, microseconds=1),
    )

    assert selected_remaining(current, (eligible,)) == [Decimal("0.60")]
    result = select_context_references(current=current, historical=(ineligible,))
    assert result.state is ContextSelectionState.NO_COMPARABLE_CYCLES


def test_tv_1602_relative_tolerance_near_reset() -> None:
    current = current_with_h(2)
    current_time = TimeToReset.from_instants(
        observed_at=current.observed_at,
        resets_at=current.resets_at,  # type: ignore[arg-type]
    )

    assert contextual_tolerance(current_time) == timedelta(minutes=6)

    eligible_observed = NOW - timedelta(days=1)
    eligible = historical_at_h(
        observed_at=eligible_observed,
        hours=2.1,
        remaining="0.60",
    )
    ineligible_observed = NOW - timedelta(days=2)
    ineligible = historical_at_h(
        observed_at=ineligible_observed,
        hours=2.1,
        remaining="0.40",
        reset_marker=ineligible_observed
        + timedelta(hours=2, minutes=6, microseconds=1),
    )

    assert selected_remaining(current, (eligible,)) == [Decimal("0.60")]
    result = select_context_references(current=current, historical=(ineligible,))
    assert result.state is ContextSelectionState.NO_COMPARABLE_CYCLES


def test_tv_1603_one_value_per_cycle_selects_nearest_real_observation() -> None:
    current = current_with_h(50.2)
    reset = NOW - timedelta(days=2) + timedelta(hours=51)
    historical = (
        historical_at_h(
            observed_at=reset - timedelta(hours=51),
            hours=51,
            remaining="0.60",
            reset_marker=reset,
        ),
        historical_at_h(
            observed_at=reset - timedelta(hours=50),
            hours=50,
            remaining="0.57",
            reset_marker=reset,
        ),
        historical_at_h(
            observed_at=reset - timedelta(hours=49),
            hours=49,
            remaining="0.55",
            reset_marker=reset,
        ),
    )

    result = select_context_references(current=current, historical=historical)

    assert result.state is ContextSelectionState.READY
    assert result.reference_set is not None
    assert result.reference_set.cycle_count == 1
    assert result.reference_set.observations[0].remaining.value == Decimal("0.57")


def test_tv_1604_equal_distance_tie_chooses_later_observed_at() -> None:
    current = current_with_h(50)
    reset = datetime(2026, 8, 9, 12, 30, tzinfo=UTC)
    early = historical_at_h(
        observed_at=datetime(2026, 8, 7, 10, 0, tzinfo=UTC),
        hours=50.5,
        remaining="0.60",
        reset_marker=reset,
    )
    late = historical_at_h(
        observed_at=datetime(2026, 8, 7, 11, 0, tzinfo=UTC),
        hours=49.5,
        remaining="0.54",
        reset_marker=reset,
    )

    assert selected_remaining(current, (early, late)) == [Decimal("0.54")]


def test_tv_1608_current_cycle_is_excluded_regardless_of_prior_polls() -> None:
    current_reset = NOW + timedelta(hours=20)
    current = observation(
        observed_at=NOW,
        resets_at=current_reset,
        remaining="0.40",
    )
    old_reset_0 = NOW - timedelta(days=4) + timedelta(hours=20)
    old_reset_1 = NOW - timedelta(days=2) + timedelta(hours=20)
    historical = (
        observation(
            observed_at=old_reset_0 - timedelta(hours=20),
            resets_at=old_reset_0,
            remaining="0.60",
        ),
        observation(
            observed_at=old_reset_1 - timedelta(hours=20),
            resets_at=old_reset_1,
            remaining="0.50",
        ),
        observation(
            observed_at=NOW - timedelta(hours=2),
            resets_at=current_reset,
            remaining="0.45",
        ),
        observation(
            observed_at=NOW - timedelta(hours=1),
            resets_at=current_reset,
            remaining="0.42",
        ),
    )

    result = select_context_references(current=current, historical=historical)

    assert result.state is ContextSelectionState.READY
    assert result.reference_set is not None
    assert {item.cycle.resets_at for item in result.reference_set.observations} == {
        old_reset_0,
        old_reset_1,
    }


def test_task_623_624_different_window_future_and_current_cycle_do_not_contribute() -> None:
    current = current_with_h(10)
    other_window = UsageWindowId("other")
    other = observation(
        observed_at=NOW - timedelta(days=1),
        resets_at=NOW - timedelta(days=1) + timedelta(hours=10),
        window_id=other_window,
    )
    future = observation(
        observed_at=NOW + timedelta(minutes=1),
        resets_at=NOW + timedelta(hours=10),
    )
    same_cycle = observation(
        observed_at=NOW - timedelta(minutes=1),
        resets_at=current.resets_at,
    )

    result = select_context_references(
        current=current,
        historical=(other, future, same_cycle),
    )

    assert result.state is ContextSelectionState.NO_COMPARABLE_CYCLES


def test_task_629_absence_states_distinguish_history_conditions() -> None:
    current = current_with_h(10)

    empty = select_context_references(current=current, historical=())
    assert empty.state is ContextSelectionState.NO_HISTORICAL_OBSERVATIONS

    missing_reset = select_context_references(
        current=current,
        historical=(
            observation(
                observed_at=NOW - timedelta(days=1),
                resets_at=None,
            ),
        ),
    )
    assert missing_reset.state is ContextSelectionState.NO_IDENTIFIABLE_CYCLES

    too_far_observed = NOW - timedelta(days=1)
    too_far = historical_at_h(
        observed_at=too_far_observed,
        hours=20,
        remaining="0.30",
    )
    no_match = select_context_references(current=current, historical=(too_far,))
    assert no_match.state is ContextSelectionState.NO_COMPARABLE_CYCLES
