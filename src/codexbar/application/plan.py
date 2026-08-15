from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from codexbar.domain.models import Fraction, UsageWindow, UsageWindowId
from codexbar.domain.quantities import FractionDelta, TimeToReset
from codexbar.domain.settings import (
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReservePolicy,
)


class PlanCheckpointResolution(StrEnum):
    NOT_CONFIGURED = "not_configured"
    RESET_MISSING = "reset_missing"
    RESET_INVALID = "reset_invalid"
    NO_ACTIVE_CHECKPOINT = "no_active_checkpoint"
    ACTIVE = "active"


class PlanCompliance(StrEnum):
    ABOVE = "above"
    AT = "at"
    BELOW = "below"


@dataclass(frozen=True, slots=True)
class WindowPlanAssessment:
    window_id: UsageWindowId
    remaining: Fraction
    reserve: Fraction | None
    time_to_reset: TimeToReset | None
    active_checkpoint: UsagePlanCheckpoint | None
    checkpoint_resolution: PlanCheckpointResolution
    effective_floor: Fraction | None
    margin: FractionDelta | None
    compliance: PlanCompliance | None


def evaluate_window_plan(
    *,
    window: UsageWindow,
    observed_at: datetime,
    reserve_policy: UsageReservePolicy,
    checkpoint_policy: UsagePlanCheckpointPolicy,
) -> WindowPlanAssessment:
    """Compare one factual Current window with explicit deterministic Plan policy."""

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")

    reserve = reserve_policy.reserve_for(window.id)
    checkpoints = checkpoint_policy.checkpoints_for(window.id)

    resolution = PlanCheckpointResolution.NOT_CONFIGURED
    time_to_reset: TimeToReset | None = None
    active_checkpoint: UsagePlanCheckpoint | None = None

    if checkpoints:
        if window.resets_at is None:
            resolution = PlanCheckpointResolution.RESET_MISSING
        else:
            try:
                time_to_reset = TimeToReset.from_instants(
                    observed_at=observed_at,
                    resets_at=window.resets_at,
                )
            except ValueError:
                resolution = PlanCheckpointResolution.RESET_INVALID
            else:
                eligible = tuple(
                    checkpoint
                    for checkpoint in checkpoints
                    if time_to_reset <= checkpoint.time_to_reset
                )
                if eligible:
                    active_checkpoint = min(
                        eligible,
                        key=lambda checkpoint: checkpoint.time_to_reset,
                    )
                    resolution = PlanCheckpointResolution.ACTIVE
                else:
                    resolution = PlanCheckpointResolution.NO_ACTIVE_CHECKPOINT

    checkpoint_floor = (
        active_checkpoint.minimum_remaining
        if active_checkpoint is not None
        else None
    )
    effective_floor = _effective_floor(reserve, checkpoint_floor)

    if effective_floor is None:
        margin = None
        compliance = None
    else:
        margin = FractionDelta(window.remaining.value - effective_floor.value)
        compliance = _compliance(window.remaining, effective_floor)

    return WindowPlanAssessment(
        window_id=window.id,
        remaining=window.remaining,
        reserve=reserve,
        time_to_reset=time_to_reset,
        active_checkpoint=active_checkpoint,
        checkpoint_resolution=resolution,
        effective_floor=effective_floor,
        margin=margin,
        compliance=compliance,
    )


def _effective_floor(
    reserve: Fraction | None,
    checkpoint_floor: Fraction | None,
) -> Fraction | None:
    candidates = tuple(
        value
        for value in (reserve, checkpoint_floor)
        if value is not None
    )
    if not candidates:
        return None
    return max(candidates, key=lambda value: value.value)


def _compliance(remaining: Fraction, floor: Fraction) -> PlanCompliance:
    if remaining.value > floor.value:
        return PlanCompliance.ABOVE
    if remaining.value == floor.value:
        return PlanCompliance.AT
    return PlanCompliance.BELOW
