from __future__ import annotations

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.domain.errors import UsageSourceError
from codexbar.domain.reset import ResetCreditReadResult


class CurrentAccountController:
    """Framework-independent current-account refresh boundary for v1.5."""

    def __init__(self, reader: AccountRateLimitsReader) -> None:
        self._reader = reader
        self._last_valid: AccountRateLimitsObservation | None = None

    @property
    def last_valid(self) -> AccountRateLimitsObservation | None:
        return self._last_valid

    def refresh(self) -> AccountRateLimitsObservation:
        try:
            observation = self._reader.read_account_rate_limits()
        except UsageSourceError:
            if self._last_valid is None:
                raise
            return AccountRateLimitsObservation(
                usage=self._last_valid.usage.as_stale(),
                reset_credits=ResetCreditReadResult.unavailable(
                    "account read failed; reset current state is unavailable"
                ),
            )

        self._last_valid = observation
        return observation
