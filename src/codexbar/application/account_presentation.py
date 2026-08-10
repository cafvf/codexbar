from __future__ import annotations

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader


class LatestAccountObservationReader:
    """Capture the latest composed read without triggering any second upstream read."""

    def __init__(self, reader: AccountRateLimitsReader) -> None:
        self._reader = reader
        self._latest: AccountRateLimitsObservation | None = None

    @property
    def latest(self) -> AccountRateLimitsObservation | None:
        return self._latest

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        observation = self._reader.read_account_rate_limits()
        self._latest = observation
        return observation
