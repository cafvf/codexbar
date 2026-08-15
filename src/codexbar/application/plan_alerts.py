from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codexbar.application.notifications import NotificationMessage, NotificationUrgency
from codexbar.application.plan import (
    PlanCheckpointResolution,
    PlanCompliance,
    WindowPlanAssessment,
    evaluate_window_plan,
)
from codexbar.application.ports import NotificationPort
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import Fraction, Freshness, UsageSnapshot, UsageWindowId
from codexbar.domain.quantities import FractionDelta
from codexbar.domain.settings import AppSettings, UsagePlanCheckpoint


@dataclass(frozen=True, slots=True)
class PlanBreachEvent:
    """One factual transition into BELOW for a single Current usage window."""

    window_id: UsageWindowId
    label: str
    remaining: Fraction
    effective_floor: Fraction
    margin: FractionDelta
    resets_at: datetime | None


@dataclass(frozen=True, slots=True)
class _RelevantPlanPolicy:
    reserve: Fraction | None
    checkpoints: tuple[UsagePlanCheckpoint, ...]


@dataclass(frozen=True, slots=True)
class _WindowTrackerState:
    policy: _RelevantPlanPolicy
    cycle_key: datetime | None
    compliance: PlanCompliance | None


class PlanAlertTransitionTracker:
    """In-memory CURRENT-only tracker for factual Plan breach transitions."""

    def __init__(self) -> None:
        self._states: dict[UsageWindowId, _WindowTrackerState] = {}

    def evaluate(
        self,
        snapshot: UsageSnapshot,
        settings: AppSettings,
    ) -> tuple[PlanBreachEvent, ...]:
        if snapshot.freshness is not Freshness.CURRENT:
            return ()

        events: list[PlanBreachEvent] = []
        for window in snapshot.windows:
            checkpoints = settings.usage_plan_checkpoints.checkpoints_for(window.id)
            assessment = evaluate_window_plan(
                window=window,
                observed_at=snapshot.observed_at,
                reserve_policy=settings.usage_reserves,
                checkpoint_policy=settings.usage_plan_checkpoints,
            )
            if checkpoints and assessment.checkpoint_resolution in {
                PlanCheckpointResolution.RESET_MISSING,
                PlanCheckpointResolution.RESET_INVALID,
            }:
                # Capability is unresolved. Preserve the previous eligible state so
                # STALE/unresolved observations cannot fabricate a transition.
                continue

            policy = _RelevantPlanPolicy(
                reserve=settings.usage_reserves.reserve_for(window.id),
                checkpoints=checkpoints,
            )
            cycle_key = window.resets_at if checkpoints else None
            previous = self._states.get(window.id)
            current_state = _WindowTrackerState(policy, cycle_key, assessment.compliance)

            if (
                previous is None
                or previous.policy != policy
                or previous.cycle_key != cycle_key
            ):
                self._states[window.id] = current_state
                continue

            self._states[window.id] = current_state
            if assessment.compliance is not PlanCompliance.BELOW:
                continue
            if previous.compliance is PlanCompliance.BELOW:
                continue

            event = _breach_event(window.label, window.resets_at, assessment)
            if event is not None:
                events.append(event)

        return tuple(events)


def _breach_event(
    label: str,
    resets_at: datetime | None,
    assessment: WindowPlanAssessment,
) -> PlanBreachEvent | None:
    floor = assessment.effective_floor
    margin = assessment.margin
    if floor is None or margin is None:
        return None
    return PlanBreachEvent(
        window_id=assessment.window_id,
        label=label,
        remaining=assessment.remaining,
        effective_floor=floor,
        margin=margin,
        resets_at=resets_at,
    )


def plan_alert_message(event: PlanBreachEvent) -> NotificationMessage:
    remaining = _percent(event.remaining)
    floor = _percent(event.effective_floor)
    margin = _percentage_points(event.margin)
    body = (
        f"{event.label}: {remaining}% remaining; "
        f"Plan floor {floor}%; margin {margin} pp."
    )
    if event.resets_at is not None:
        reset = event.resets_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")
        body = f"{body} Resets {reset}."
    return NotificationMessage(
        "CodexBar Plan breach",
        body,
        NotificationUrgency.NORMAL,
    )


class PlanAlertService:
    """Evaluate Plan transitions and deliver factual notifications through the shared port."""

    def __init__(
        self,
        notifier: NotificationPort,
        settings: AppSettings,
        tracker: PlanAlertTransitionTracker | None = None,
    ) -> None:
        self._notifier = notifier
        self._settings = settings
        self._tracker = tracker or PlanAlertTransitionTracker()

    def apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings

    def process(
        self,
        snapshot: UsageSnapshot,
        *,
        notifications_enabled: bool,
    ) -> tuple[PlanBreachEvent, ...]:
        events = self._tracker.evaluate(snapshot, self._settings)
        delivery_enabled = (
            notifications_enabled
            and self._settings.plan_breach_notifications_enabled
        )
        if not delivery_enabled:
            return events

        for event in events:
            try:
                self._notifier.notify(plan_alert_message(event))
            except NotificationDeliveryError:
                continue
        return events


def _percent(value: Fraction) -> str:
    return format(value.percent.normalize(), "f")


def _percentage_points(value: FractionDelta) -> str:
    points = value.value * 100
    return format(points.normalize(), "+f")
