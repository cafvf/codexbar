from datetime import UTC, datetime, timedelta

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.budget import BudgetRuntime
from codexbar.application.reset_monitor import ResetExpiryMonitor, build_reset_situation
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import UsageSnapshot, UsageSource
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


def test_horizon_crossings_are_deduplicated_and_nonexpiring_has_no_expiry_fact() -> None:
    details = (
        ResetCreditDetail(
            ResetCreditId("A"),
            "codexRateLimits",
            "available",
            NOW,
            ExpiryKnowledge.expires_at(NOW + timedelta(hours=5)),
        ),
        ResetCreditDetail(
            ResetCreditId("B"),
            "codexRateLimits",
            "available",
            NOW,
            ExpiryKnowledge.does_not_expire(),
        ),
    )
    observation = AccountRateLimitsObservation(
        UsageSnapshot((), NOW, UsageSource.MOCK),
        ResetCreditReadResult.current(
            ResetCreditInventory(
                NOW,
                2,
                DetailCoverage.DETAILS_COMPLETE,
                details,
            )
        ),
    )
    situation = build_reset_situation(
        observation,
        BudgetRuntime(AppSettings.defaults()),
        ResetLedgerProjection(),
    )
    monitor = ResetExpiryMonitor()

    first = monitor.evaluate(situation, now=NOW)
    second = monitor.evaluate(situation, now=NOW)

    assert any(fact.key == "A:6h" for fact in first)
    assert not any(fact.key.startswith("B:") and "h" in fact.key for fact in first)
    assert second == ()
