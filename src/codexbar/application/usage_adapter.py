from __future__ import annotations

from dataclasses import dataclass

from codexbar.application.account import AccountRateLimitsReader
from codexbar.domain.models import UsageSnapshot


@dataclass(frozen=True, slots=True)
class AccountUsageProvider:
    """Compatibility projection from one composed account read to canonical usage."""

    reader: AccountRateLimitsReader

    def get_usage(self) -> UsageSnapshot:
        return self.reader.read_account_rate_limits().usage
