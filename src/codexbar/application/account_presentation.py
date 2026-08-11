from __future__ import annotations

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.domain.errors import UsageError
from codexbar.domain.reset import ResetCreditReadResult


class LatestAccountObservationReader:
    """Capture one coherent account observation for all Current-derived surfaces."""

    def __init__(self, reader: AccountRateLimitsReader) -> None:
        self._reader = reader
        self._latest: AccountRateLimitsObservation | None = None

    @property
    def latest(self) -> AccountRateLimitsObservation | None:
        return self._latest

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        try:
            observation = self._reader.read_account_rate_limits()
        except UsageError:
            self._mark_latest_stale()
            raise
        self._latest = observation
        return observation

    def _mark_latest_stale(self) -> None:
        latest = self._latest
        if latest is None:
            return
        self._latest = AccountRateLimitsObservation(
            usage=latest.usage.as_stale(),
            reset_credits=ResetCreditReadResult.unavailable(
                "account read failed; reset current state is unavailable"
            ),
        )
