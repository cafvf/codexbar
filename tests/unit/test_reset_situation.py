from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.budget import BudgetRuntime
from codexbar.application.reset_monitor import build_reset_situation
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.reset import ResetCreditReadResult
from codexbar.domain.settings import AppSettings


def test_situation_does_not_infer_unavailable_reset_details() -> None:
    observation = AccountRateLimitsObservation(
        UsageSnapshot(
            (
                UsageWindow(
                    UsageWindowId("window_300m"),
                    "5 hours",
                    Fraction(Decimal("0.50")),
                ),
            ),
            datetime(2026, 8, 10, tzinfo=UTC),
            UsageSource.MOCK,
        ),
        ResetCreditReadResult.unavailable("missing"),
    )

    situation = build_reset_situation(
        observation,
        BudgetRuntime(AppSettings.defaults()),
        ResetLedgerProjection(),
    )

    assert situation.known_details == ()
