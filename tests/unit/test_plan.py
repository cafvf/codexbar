from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.plan import (
    PlanCheckpointResolution,
    PlanCompliance,
    evaluate_window_plan,
)
from codexbar.domain.models import Fraction, UsageWindow, UsageWindowId
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import (
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)

OBSERVED_AT = datetime(2026, 8, 14, 12, tzinfo=UTC)
WINDOW_ID = UsageWindowId("opaque-weekly")


def fraction(value: str) -> Fraction:
    return Fraction(Decimal(value))


def checkpoint(
    hours: int,
    minimum: str,
    *,
    window_id: UsageWindowId = WINDOW_ID,
) -> UsagePlanCheckpoint:
    return UsagePlanCheckpoint(
        window_id=window_id,
        time_to_reset=TimeToReset(timedelta(hours=hours)),
        minimum_remaining=fraction(minimum),
    )


def test_checkpoint_policy_is_canonical_and_keyed_by_opaque_window_id() -> None:
    alpha = UsageWindowId("alpha")
    zeta = UsageWindowId("zeta")
    policy = UsagePlanCheckpointPolicy(
        (
            checkpoint(24, "0.30", window_id=alpha),
            checkpoint(72, "0.40", window_id=zeta),
            checkpoint(0, "0.20", window_id=alpha),
            checkpoint(72, "0.55", window_id=alpha),
        )
    )

    assert [
        (entry.window_id.value, entry.time_to_reset.duration)
        for entry in policy.entries
    ] == [
        ("alpha", timedelta(hours=72)),
        ("alpha", timedelta(hours=24)),
        ("alpha", timedelta(0)),
        ("zeta", timedelta(hours=72)),
    ]
    assert policy.checkpoints_for(alpha) == policy.entries[:3]
    assert policy.checkpoints_for(UsageWindowId("missing")) == ()


def test_duplicate_checkpoint_coordinate_for_one_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        UsagePlanCheckpointPolicy(
            (
                checkpoint(72, "0.55"),
                checkpoint(72, "0.40"),
            )
        )


def test_same_checkpoint_coordinate_for_different_windows_is_allowed() -> None:
    other = UsageWindowId("opaque-other")
    policy = UsagePlanCheckpointPolicy(
        (
            checkpoint(72, "0.55"),
            checkpoint(72, "0.40", window_id=other),
        )
    )

    assert len(policy.entries) == 2


def test_checkpoint_requires_whole_second_coordinate() -> None:
    with pytest.raises(ValueError, match="whole seconds"):
        UsagePlanCheckpoint(
            WINDOW_ID,
            TimeToReset(timedelta(seconds=1, microseconds=1)),
            fraction("0.55"),
        )


def test_non_monotonic_checkpoint_floors_are_valid_policy() -> None:
    policy = UsagePlanCheckpointPolicy(
        (
            checkpoint(72, "0.40"),
            checkpoint(24, "0.60"),
        )
    )

    assert [entry.minimum_remaining.value for entry in policy.entries] == [
        Decimal("0.40"),
        Decimal("0.60"),
    ]


PLAN_VECTORS = [
    (
        "P01", None, (), 5, "0.63",
        PlanCheckpointResolution.NOT_CONFIGURED, None, None, None, None,
    ),
    (
        "P02", "0.15", (), None, "0.63",
        PlanCheckpointResolution.NOT_CONFIGURED, "0.15", "0.48",
        PlanCompliance.ABOVE, None,
    ),
    (
        "P03", None, ((72, "0.55"),), 100, "0.63",
        PlanCheckpointResolution.NO_ACTIVE_CHECKPOINT, None, None, None, None,
    ),
    (
        "P04", None, ((72, "0.55"),), 72, "0.55",
        PlanCheckpointResolution.ACTIVE, "0.55", "0.00",
        PlanCompliance.AT, "0.55",
    ),
    (
        "P05", None, ((72, "0.55"), (24, "0.30")), 60, "0.50",
        PlanCheckpointResolution.ACTIVE, "0.55", "-0.05",
        PlanCompliance.BELOW, "0.55",
    ),
    (
        "P06", "0.60", ((72, "0.55"),), 60, "0.63",
        PlanCheckpointResolution.ACTIVE, "0.60", "0.03",
        PlanCompliance.ABOVE, "0.55",
    ),
    (
        "P07", "0.15", ((72, "0.55"),), 60, "0.63",
        PlanCheckpointResolution.ACTIVE, "0.55", "0.08",
        PlanCompliance.ABOVE, "0.55",
    ),
    (
        "P08", "0.55", ((72, "0.55"),), 60, "0.55",
        PlanCheckpointResolution.ACTIVE, "0.55", "0.00",
        PlanCompliance.AT, "0.55",
    ),
    (
        "P09", "0.15", ((72, "0.55"),), None, "0.12",
        PlanCheckpointResolution.RESET_MISSING, "0.15", "-0.03",
        PlanCompliance.BELOW, None,
    ),
    (
        "P10", None, ((72, "0.55"),), None, "0.63",
        PlanCheckpointResolution.RESET_MISSING, None, None, None, None,
    ),
    (
        "P11", "0.15", ((72, "0.55"),), -1, "0.20",
        PlanCheckpointResolution.RESET_INVALID, "0.15", "0.05",
        PlanCompliance.ABOVE, None,
    ),
    (
        "P12", None, ((72, "0.40"), (24, "0.60")), 20, "0.55",
        PlanCheckpointResolution.ACTIVE, "0.60", "-0.05",
        PlanCompliance.BELOW, "0.60",
    ),
    (
        "P13", "0.15", ((72, "0.55"),), 80, "0.10",
        PlanCheckpointResolution.NO_ACTIVE_CHECKPOINT, "0.15", "-0.05",
        PlanCompliance.BELOW, None,
    ),
    (
        "P14", None, ((0, "0.10"),), 0, "0.10",
        PlanCheckpointResolution.ACTIVE, "0.10", "0.00",
        PlanCompliance.AT, "0.10",
    ),
]


@pytest.mark.parametrize(
    (
        "vector",
        "reserve",
        "checkpoint_rows",
        "reset_hours",
        "remaining",
        "resolution",
        "floor",
        "margin",
        "compliance",
        "active_minimum",
    ),
    PLAN_VECTORS,
    ids=[row[0] for row in PLAN_VECTORS],
)
def test_canonical_plan_vectors(
    vector: str,
    reserve: str | None,
    checkpoint_rows: tuple[tuple[int, str], ...],
    reset_hours: int | None,
    remaining: str,
    resolution: PlanCheckpointResolution,
    floor: str | None,
    margin: str | None,
    compliance: PlanCompliance | None,
    active_minimum: str | None,
) -> None:
    del vector
    reserve_policy = UsageReservePolicy(
        () if reserve is None else (UsageReserve(WINDOW_ID, fraction(reserve)),)
    )
    checkpoint_policy = UsagePlanCheckpointPolicy(
        tuple(checkpoint(hours, minimum) for hours, minimum in checkpoint_rows)
    )
    resets_at = (
        None
        if reset_hours is None
        else OBSERVED_AT + timedelta(hours=reset_hours)
    )
    window = UsageWindow(
        WINDOW_ID,
        "Weekly",
        fraction(remaining),
        resets_at=resets_at,
    )

    assessment = evaluate_window_plan(
        window=window,
        observed_at=OBSERVED_AT,
        reserve_policy=reserve_policy,
        checkpoint_policy=checkpoint_policy,
    )

    assert assessment.window_id == WINDOW_ID
    assert assessment.remaining == fraction(remaining)
    assert assessment.checkpoint_resolution is resolution
    assert assessment.effective_floor == (
        None if floor is None else fraction(floor)
    )
    if margin is None:
        assert assessment.margin is None
    else:
        assert assessment.margin is not None
        assert assessment.margin.value == Decimal(margin)
    assert assessment.compliance is compliance
    assert (
        None
        if assessment.active_checkpoint is None
        else assessment.active_checkpoint.minimum_remaining
    ) == (None if active_minimum is None else fraction(active_minimum))

    if checkpoint_rows and reset_hours is not None and reset_hours >= 0:
        assert assessment.time_to_reset == TimeToReset(timedelta(hours=reset_hours))
    else:
        assert assessment.time_to_reset is None


def test_evaluator_rejects_naive_observation_timestamp() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        evaluate_window_plan(
            window=UsageWindow(WINDOW_ID, "Weekly", fraction("0.63")),
            observed_at=datetime(2026, 8, 14, 12),
            reserve_policy=UsageReservePolicy(),
            checkpoint_policy=UsagePlanCheckpointPolicy(),
        )
