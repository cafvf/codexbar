from decimal import Decimal

from codexbar.application.budget import BudgetStatus, calculate_window_budget
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import UsageReservePolicy

WINDOW = UsageWindowId("window_10080m")


def _policy(value: str) -> UsageReservePolicy:
    return UsageReservePolicy().with_reserve(WINDOW, Fraction(Decimal(value)))


def test_budget_status_and_exact_headroom_boundaries() -> None:
    above = calculate_window_budget(WINDOW, Fraction(Decimal("0.43")), _policy("0.15"))
    at = calculate_window_budget(WINDOW, Fraction(Decimal("0.15")), _policy("0.15"))
    below = calculate_window_budget(WINDOW, Fraction(Decimal("0.10")), _policy("0.15"))

    assert above.status is BudgetStatus.ABOVE_RESERVE
    assert above.headroom == Fraction(Decimal("0.28"))
    assert at.status is BudgetStatus.AT_RESERVE
    assert at.headroom == Fraction(Decimal("0"))
    assert below.status is BudgetStatus.BELOW_RESERVE
    assert below.headroom == Fraction(Decimal("0"))


def test_no_policy_differs_from_explicit_zero_reserve() -> None:
    remaining = Fraction(Decimal("0.40"))

    none = calculate_window_budget(WINDOW, remaining, UsageReservePolicy())
    zero = calculate_window_budget(WINDOW, remaining, _policy("0"))

    assert none.status is BudgetStatus.NO_POLICY
    assert none.reserve is None
    assert zero.status is BudgetStatus.ABOVE_RESERVE
    assert zero.headroom == remaining


def test_unknown_window_does_not_inherit_other_policy() -> None:
    result = calculate_window_budget(
        UsageWindowId("window_new"),
        Fraction(Decimal("0.40")),
        _policy("0.15"),
    )

    assert result.status is BudgetStatus.NO_POLICY
