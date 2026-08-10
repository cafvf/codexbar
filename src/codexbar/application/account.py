from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codexbar.domain.models import UsageSnapshot
from codexbar.domain.reset import ResetCreditReadResult


@dataclass(frozen=True, slots=True)
class AccountRateLimitsObservation:
    """Current account-rate-limit state obtained from one upstream read boundary."""

    usage: UsageSnapshot
    reset_credits: ResetCreditReadResult


class AccountRateLimitsReader(Protocol):
    """Read-only port for the composed current account-rate-limit observation."""

    def read_account_rate_limits(self) -> AccountRateLimitsObservation: ...


class ResetCreditConsumer(Protocol):
    """Segregated reset-credit side-effect port reserved for Phase D.

    TASK-511 establishes the destructive capability as a separate application boundary without
    prematurely freezing consume command/outcome types. The callable contract is added when those
    normalized types are introduced by the redeem implementation tasks.
    """
