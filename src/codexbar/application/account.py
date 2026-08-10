from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.models import UsageSnapshot
from codexbar.domain.reset import ResetCreditId, ResetCreditReadResult


@dataclass(frozen=True, slots=True)
class AccountRateLimitsObservation:
    """Current account-rate-limit state obtained from one upstream read boundary."""

    usage: UsageSnapshot
    reset_credits: ResetCreditReadResult


class AccountRateLimitsReader(Protocol):
    """Read-only port for the composed current account-rate-limit observation."""

    def read_account_rate_limits(self) -> AccountRateLimitsObservation: ...


class ResetConsumeOutcome(StrEnum):
    RESET = "reset"
    ALREADY_REDEEMED = "alreadyRedeemed"
    NOTHING_TO_RESET = "nothingToReset"
    NO_CREDIT = "noCredit"


@dataclass(frozen=True, slots=True)
class ResetConsumeCommand:
    attempt_id: RedeemAttemptId
    credit_id: ResetCreditId | None = None


class ResetCreditConsumer(Protocol):
    """Segregated destructive port for one explicit reset-credit consume operation."""

    def consume_reset_credit(self, command: ResetConsumeCommand) -> ResetConsumeOutcome: ...
