from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.budget import BudgetRuntime, WindowBudget
from codexbar.application.redeem import RedeemAttempt, RedeemProcessManager
from codexbar.application.reset_monitor import (
    ResetAdvice,
    ResetOpportunityPolicy,
    build_reset_situation,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKind,
    ResetCreditDetail,
    ResetCreditReadStatus,
)
from codexbar.domain.settings import AppSettings
from codexbar.ui.viewmodel import UsageViewModel, UsageViewState


class ResetCurrentKind(StrEnum):
    UNAVAILABLE = "unavailable"
    COUNT_ONLY = "count_only"
    PARTIAL = "partial"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class ResetCreditItemViewState:
    credit_id: str
    title: str
    expiry_text: str


@dataclass(frozen=True, slots=True)
class ResetCurrentViewState:
    kind: ResetCurrentKind
    available_count: int | None
    credits: tuple[ResetCreditItemViewState, ...]
    diagnostic: str | None = None


@dataclass(frozen=True, slots=True)
class BudgetViewState:
    windows: tuple[WindowBudget, ...]
    advice: ResetAdvice


@dataclass(frozen=True, slots=True)
class RedeemActionViewState:
    available: bool
    unresolved: tuple[RedeemAttempt, ...]


@dataclass(frozen=True, slots=True)
class CurrentAccountViewState:
    usage: UsageViewState
    reset: ResetCurrentViewState
    budget: BudgetViewState
    redeem: RedeemActionViewState


ProjectionProvider = Callable[[], ResetLedgerProjection]
Clock = Callable[[], datetime]


class CurrentAccountPresenter:
    def __init__(
        self,
        latest_reader: LatestAccountObservationReader,
        settings: AppSettings,
        projection_provider: ProjectionProvider,
        *,
        redeem_manager: RedeemProcessManager | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._latest_reader = latest_reader
        self._budget_runtime = BudgetRuntime(settings)
        self._projection_provider = projection_provider
        self._redeem_manager = redeem_manager
        self._policy = ResetOpportunityPolicy()
        self._clock = clock or datetime.now

    def apply_settings(self, settings: AppSettings) -> None:
        self._budget_runtime.apply_settings(settings)

    def current(self) -> CurrentAccountViewState | None:
        observation = self._latest_reader.latest
        if observation is None:
            return None

        projection = self._projection_provider()
        situation = build_reset_situation(
            observation,
            self._budget_runtime,
            projection,
        )
        advice = self._policy.assess(
            situation,
            now=self._aware_now(observation),
        )
        unresolved = (
            self._redeem_manager.unresolved_attempts()
            if self._redeem_manager is not None
            else ()
        )
        return CurrentAccountViewState(
            usage=UsageViewModel.from_snapshot(observation.usage),
            reset=_reset_view(observation),
            budget=BudgetViewState(situation.budgets, advice),
            redeem=RedeemActionViewState(
                available=self._redeem_manager is not None,
                unresolved=unresolved,
            ),
        )

    def _aware_now(self, observation: AccountRateLimitsObservation) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            return observation.usage.observed_at
        return value


def _reset_view(observation: AccountRateLimitsObservation) -> ResetCurrentViewState:
    result = observation.reset_credits
    if result.status is not ResetCreditReadStatus.CURRENT or result.inventory is None:
        return ResetCurrentViewState(
            ResetCurrentKind.UNAVAILABLE,
            None,
            (),
            result.diagnostic,
        )

    inventory = result.inventory
    kind = {
        DetailCoverage.COUNT_ONLY: ResetCurrentKind.COUNT_ONLY,
        DetailCoverage.DETAILS_PARTIAL: ResetCurrentKind.PARTIAL,
        DetailCoverage.DETAILS_COMPLETE: ResetCurrentKind.COMPLETE,
    }[inventory.detail_coverage]
    return ResetCurrentViewState(
        kind,
        inventory.available_count,
        tuple(_credit_view(detail) for detail in inventory.credits),
    )


def _credit_view(detail: ResetCreditDetail) -> ResetCreditItemViewState:
    title = detail.title or detail.credit_id.value
    if detail.expiry.kind is ExpiryKind.DOES_NOT_EXPIRE:
        expiry = "Does not expire"
    elif detail.expiry.instant is not None:
        expiry = detail.expiry.instant.astimezone().strftime("%Y-%m-%d %H:%M %Z")
    else:
        expiry = "Expiry unavailable"
    return ResetCreditItemViewState(detail.credit_id.value, title, expiry)
