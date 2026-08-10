from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.budget import BudgetRuntime
from codexbar.application.reset_monitor import (
    OpportunityPriority,
    ResetOpportunityPolicy,
    build_reset_situation,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
    ResetCreditReadResult,
)
from codexbar.domain.settings import AppSettings

NOW = datetime(2026, 8, 10, 12, tzinfo=UTC)


def situation(expiry_hours: int, reserve: str = "0.10"):
    window = UsageWindow(
        UsageWindowId("window_300m"),
        "5 hours",
        Fraction(Decimal("0.50")),
        NOW + timedelta(hours=10),
    )
    observation = AccountRateLimitsObservation(
        UsageSnapshot((window,), NOW, UsageSource.MOCK),
        ResetCreditReadResult.current(
            ResetCreditInventory(
                NOW,
                1,
                DetailCoverage.DETAILS_COMPLETE,
                (
                    ResetCreditDetail(
                        ResetCreditId("A"),
                        "codexRateLimits",
                        "available",
                        NOW,
                        ExpiryKnowledge.expires_at(
                            NOW + timedelta(hours=expiry_hours)
                        ),
                    ),
                ),
            )
        ),
    )
    settings = AppSettings.defaults().with_usage_reserve(
        window.id,
        Fraction(Decimal(reserve)),
    )
    return build_reset_situation(
        observation,
        BudgetRuntime(settings),
        ResetLedgerProjection(),
    )


def test_exact_horizon_boundaries() -> None:
    policy = ResetOpportunityPolicy()

    assert policy.assess(situation(24), now=NOW).priority is OpportunityPriority.WATCH
    assert policy.assess(situation(6), now=NOW).priority is OpportunityPriority.HIGH
