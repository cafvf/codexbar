from __future__ import annotations

from decimal import Decimal

from codexbar.application.budget import BudgetStatus, calculate_window_budget
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import UsageReservePolicy


def test_task_764_no_policy_headroom_is_not_applicable_not_zero() -> None:
    budget = calculate_window_budget(
        UsageWindowId("dynamic"),
        Fraction(Decimal("0.63")),
        UsageReservePolicy(),
    )
    assert budget.status is BudgetStatus.NO_POLICY
    assert budget.reserve is None
    assert budget.headroom is None
