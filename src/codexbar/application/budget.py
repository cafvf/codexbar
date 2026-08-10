from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from codexbar.domain.models import Fraction, UsageWindow, UsageWindowId
from codexbar.domain.settings import AppSettings, UsageReservePolicy


class BudgetStatus(StrEnum):
    NO_POLICY = "no_policy"
    ABOVE_RESERVE = "above_reserve"
    AT_RESERVE = "at_reserve"
    BELOW_RESERVE = "below_reserve"


@dataclass(frozen=True, slots=True)
class WindowBudget:
    window_id: UsageWindowId
    remaining: Fraction
    reserve: Fraction | None
    headroom: Fraction
    status: BudgetStatus


def calculate_window_budget(
    window_id: UsageWindowId,
    remaining: Fraction,
    policy: UsageReservePolicy,
) -> WindowBudget:
    reserve = policy.reserve_for(window_id)
    if reserve is None:
        return WindowBudget(
            window_id=window_id,
            remaining=remaining,
            reserve=None,
            headroom=Fraction(Decimal("0")),
            status=BudgetStatus.NO_POLICY,
        )

    difference = remaining.value - reserve.value
    headroom = Fraction(max(difference, Decimal("0")))
    if remaining.value > reserve.value:
        status = BudgetStatus.ABOVE_RESERVE
    elif remaining.value == reserve.value:
        status = BudgetStatus.AT_RESERVE
    else:
        status = BudgetStatus.BELOW_RESERVE

    return WindowBudget(
        window_id=window_id,
        remaining=remaining,
        reserve=reserve,
        headroom=headroom,
        status=status,
    )


class BudgetRuntime:
    """Current settings-backed budget assessment that can update without restart."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings

    def assess(self, window: UsageWindow) -> WindowBudget:
        return calculate_window_budget(
            window.id,
            window.remaining,
            self._settings.usage_reserves,
        )
