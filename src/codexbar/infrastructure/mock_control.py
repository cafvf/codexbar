from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.account import (
    AccountRateLimitsObservation,
    ResetConsumeCommand,
    ResetConsumeOutcome,
)
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
    ResetCreditReadResult,
)


class MockAccountRateLimitsReader:
    def __init__(self) -> None:
        self.calls = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.calls += 1
        now = datetime(2026, 8, 10, 12, tzinfo=UTC)
        return AccountRateLimitsObservation(
            UsageSnapshot(
                (
                    UsageWindow(
                        UsageWindowId("window_300m"),
                        "5 hours",
                        Fraction(Decimal("0.72")),
                        now + timedelta(hours=2),
                    ),
                    UsageWindow(
                        UsageWindowId("window_10080m"),
                        "Weekly",
                        Fraction(Decimal("0.44")),
                        now + timedelta(days=3),
                    ),
                ),
                now,
                UsageSource.MOCK,
            ),
            ResetCreditReadResult.current(
                ResetCreditInventory(
                    now,
                    2,
                    DetailCoverage.DETAILS_COMPLETE,
                    (
                        ResetCreditDetail(
                            ResetCreditId("mock-expiring"),
                            "codexRateLimits",
                            "available",
                            now - timedelta(days=1),
                            ExpiryKnowledge.expires_at(now + timedelta(hours=8)),
                            "Mock expiring reset",
                        ),
                        ResetCreditDetail(
                            ResetCreditId("mock-banked"),
                            "codexRateLimits",
                            "available",
                            now - timedelta(days=2),
                            ExpiryKnowledge.does_not_expire(),
                            "Mock non-expiring reset",
                        ),
                    ),
                )
            ),
        )


class MockResetCreditConsumer:
    def __init__(self) -> None:
        self.commands: list[ResetConsumeCommand] = []

    def consume_reset_credit(self, command: ResetConsumeCommand) -> ResetConsumeOutcome:
        self.commands.append(command)
        return ResetConsumeOutcome.RESET
