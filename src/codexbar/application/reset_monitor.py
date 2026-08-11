from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.budget import BudgetRuntime, BudgetStatus, WindowBudget
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import Freshness
from codexbar.domain.reset import ExpiryKind, ResetCreditDetail, ResetCreditReadStatus

WATCH_HORIZON = timedelta(hours=24)
URGENT_HORIZON = timedelta(hours=6)
SCHEDULED_RESET_NEAR = timedelta(hours=2)
MEANINGFUL_HEADROOM_POINTS = 5


class ResetFactKind(StrEnum):
    CREDIT_DISCOVERED = "credit_discovered"
    COUNT_CHANGED = "count_changed"
    EXPIRY_24H = "expiry_24h"
    EXPIRY_6H = "expiry_6h"
    EXPIRY_1H = "expiry_1h"


class OpportunityPriority(StrEnum):
    NONE = "none"
    WATCH = "watch"
    URGENT = "urgent"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ResetSituation:
    observation: AccountRateLimitsObservation
    budgets: tuple[WindowBudget, ...]
    known_details: tuple[ResetCreditDetail, ...]
    unresolved_redeem_attempts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResetAdvice:
    priority: OpportunityPriority
    reason: str


@dataclass(frozen=True, slots=True)
class ResetFact:
    kind: ResetFactKind
    key: str
    body: str


def build_reset_situation(
    observation: AccountRateLimitsObservation,
    budget_runtime: BudgetRuntime,
    projection: ResetLedgerProjection,
) -> ResetSituation:
    budgets = tuple(budget_runtime.assess(window) for window in observation.usage.windows)

    known_details: tuple[ResetCreditDetail, ...]
    if (
        observation.reset_credits.status is ResetCreditReadStatus.CURRENT
        and observation.reset_credits.inventory is not None
    ):
        known_details = observation.reset_credits.inventory.credits
    else:
        known_details = ()

    return ResetSituation(
        observation,
        budgets,
        known_details,
        projection.unresolved_attempt_ids,
    )


class ResetOpportunityPolicy:
    def assess(self, situation: ResetSituation, *, now: datetime) -> ResetAdvice:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("policy clock must be timezone-aware")
        if situation.observation.usage.freshness is not Freshness.CURRENT:
            return ResetAdvice(OpportunityPriority.NONE, "usage is not current")
        if situation.unresolved_redeem_attempts:
            return ResetAdvice(
                OpportunityPriority.URGENT,
                "an unresolved redeem attempt requires recovery",
            )

        nearest = _nearest_upcoming_expiry(situation.known_details, now)
        meaningful = _has_meaningful_headroom(situation.budgets)
        scheduled_reset_near = _has_near_scheduled_reset(situation, now)

        if nearest is not None and nearest <= URGENT_HORIZON:
            return ResetAdvice(
                OpportunityPriority.HIGH if meaningful else OpportunityPriority.URGENT,
                "known reset credit expires within 6 hours",
            )
        if scheduled_reset_near and meaningful:
            return ResetAdvice(
                OpportunityPriority.HIGH,
                "scheduled usage reset is near and usable headroom is meaningful",
            )
        if nearest is not None and nearest <= WATCH_HORIZON:
            return ResetAdvice(
                OpportunityPriority.WATCH,
                "known reset credit expires within 24 hours",
            )
        return ResetAdvice(OpportunityPriority.NONE, "no current reset opportunity signal")


def _nearest_upcoming_expiry(
    details: tuple[ResetCreditDetail, ...],
    now: datetime,
) -> timedelta | None:
    remaining = (
        detail.expiry.instant - now
        for detail in details
        if detail.expiry.kind is ExpiryKind.EXPIRES_AT
        and detail.expiry.instant is not None
        and detail.expiry.instant >= now
    )
    return min(remaining, default=None)


def _has_meaningful_headroom(budgets: tuple[WindowBudget, ...]) -> bool:
    return any(
        budget.status is BudgetStatus.ABOVE_RESERVE
        and budget.headroom.percent >= MEANINGFUL_HEADROOM_POINTS
        for budget in budgets
    )


def _has_near_scheduled_reset(situation: ResetSituation, now: datetime) -> bool:
    return any(
        window.resets_at is not None
        and timedelta(0) <= window.resets_at - now <= SCHEDULED_RESET_NEAR
        for window in situation.observation.usage.windows
    )


class ResetExpiryMonitor:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._last_count: int | None = None
        self._known_credit_ids: set[str] = set()

    def evaluate(
        self,
        situation: ResetSituation,
        *,
        now: datetime,
    ) -> tuple[ResetFact, ...]:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("monitor clock must be timezone-aware")
        facts: list[ResetFact] = []

        result = situation.observation.reset_credits
        if result.status is ResetCreditReadStatus.CURRENT and result.inventory is not None:
            count = result.inventory.available_count
            if self._last_count is not None and count != self._last_count:
                facts.append(
                    ResetFact(
                        ResetFactKind.COUNT_CHANGED,
                        f"count:{self._last_count}->{count}",
                        f"Reset-credit available count changed from {self._last_count} to {count}.",
                    )
                )
            self._last_count = count

        for detail in situation.known_details:
            credit_id = detail.credit_id.value
            if credit_id not in self._known_credit_ids:
                facts.append(
                    ResetFact(
                        ResetFactKind.CREDIT_DISCOVERED,
                        f"credit:{credit_id}",
                        f"Reset credit {credit_id} was discovered.",
                    )
                )
                self._known_credit_ids.add(credit_id)

            if detail.expiry.kind is not ExpiryKind.EXPIRES_AT or detail.expiry.instant is None:
                continue

            remaining = detail.expiry.instant - now
            for hours, kind in (
                (24, ResetFactKind.EXPIRY_24H),
                (6, ResetFactKind.EXPIRY_6H),
                (1, ResetFactKind.EXPIRY_1H),
            ):
                if timedelta(0) <= remaining <= timedelta(hours=hours):
                    key = f"{credit_id}:{hours}h"
                    if key not in self._seen:
                        facts.append(
                            ResetFact(
                                kind,
                                key,
                                f"Reset credit {credit_id} expires within {hours}h.",
                            )
                        )
                        self._seen.add(key)

        return tuple(facts)
