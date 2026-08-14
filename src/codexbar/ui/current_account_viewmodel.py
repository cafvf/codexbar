from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.budget import BudgetRuntime, WindowBudget
from codexbar.application.redeem import RedeemAttempt, RedeemProcessManager
from codexbar.application.redeem_execution import RedeemExecutionController
from codexbar.application.reset_ledger import ResetLedgerError
from codexbar.application.reset_monitor import (
    OpportunityPriority,
    ResetAdvice,
    ResetOpportunityPolicy,
    build_reset_situation,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.application.runtime_health import RuntimeDiagnosticRegistry
from codexbar.domain.models import Freshness
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKind,
    ResetCreditDetail,
    ResetCreditReadStatus,
)
from codexbar.domain.settings import AppSettings
from codexbar.ui.context_controller import ContextController
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter
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


def _withheld_control_advice() -> ResetAdvice:
    return ResetAdvice(
        OpportunityPriority.NONE,
        "reset ledger unavailable; control advice is withheld",
    )


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
        self._clock = clock or (lambda: datetime.now(UTC))
        self.runtime_context_controller: ContextController | None = None
        self.runtime_redeem_controller: RedeemExecutionController | None = None
        self.runtime_health_presenter: SystemHealthPresenter | None = None
        self.runtime_diagnostics: RuntimeDiagnosticRegistry | None = None

    def bind_runtime_surfaces(
        self,
        *,
        context_controller: ContextController,
        redeem_controller: RedeemExecutionController | None,
        health_presenter: SystemHealthPresenter,
        diagnostics: RuntimeDiagnosticRegistry,
    ) -> None:
        self.runtime_context_controller = context_controller
        self.runtime_redeem_controller = redeem_controller
        self.runtime_health_presenter = health_presenter
        self.runtime_diagnostics = diagnostics

    def apply_settings(self, settings: AppSettings) -> None:
        self._budget_runtime.apply_settings(settings)

    def current(self) -> CurrentAccountViewState | None:
        observation = self._latest_reader.latest
        if observation is None:
            return None

        projection, ledger_available = self._projection()
        unresolved, ledger_available = self._unresolved_attempts(ledger_available)
        budget = self._budget_view(observation, projection, ledger_available)
        redeem_available = (
            self._redeem_manager is not None
            and ledger_available
            and observation.usage.freshness is Freshness.CURRENT
        )
        return CurrentAccountViewState(
            usage=UsageViewModel.from_snapshot(observation.usage),
            reset=_reset_view(observation),
            budget=budget,
            redeem=RedeemActionViewState(
                available=redeem_available,
                unresolved=unresolved,
            ),
        )

    def _projection(self) -> tuple[ResetLedgerProjection, bool]:
        try:
            return self._projection_provider(), True
        except ResetLedgerError:
            return ResetLedgerProjection(), False

    def _unresolved_attempts(
        self,
        ledger_available: bool,
    ) -> tuple[tuple[RedeemAttempt, ...], bool]:
        manager = self._redeem_manager
        if manager is None or not ledger_available:
            return (), ledger_available
        try:
            return manager.unresolved_attempts(), True
        except ResetLedgerError:
            return (), False

    def _budget_view(
        self,
        observation: AccountRateLimitsObservation,
        projection: ResetLedgerProjection,
        ledger_available: bool,
    ) -> BudgetViewState:
        if observation.usage.freshness is not Freshness.CURRENT:
            return BudgetViewState(
                (),
                ResetAdvice(
                    OpportunityPriority.NONE,
                    "usage is not current; control and budget are withheld",
                ),
            )

        situation = build_reset_situation(
            observation,
            self._budget_runtime,
            projection,
        )
        advice = (
            self._policy.assess(situation, now=self._aware_now())
            if ledger_available
            else _withheld_control_advice()
        )
        return BudgetViewState(situation.budgets, advice)

    def _aware_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("current-account presenter clock must be timezone-aware")
        return value.astimezone(UTC)


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
