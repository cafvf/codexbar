from __future__ import annotations

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.application.history_runtime import HistoryService


class CapturingAccountRateLimitsReader:
    """Capture current usage history from the same composed account read."""

    def __init__(
        self,
        reader: AccountRateLimitsReader,
        history_service: HistoryService,
    ) -> None:
        self._reader = reader
        self._history_service = history_service

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        observation = self._reader.read_account_rate_limits()
        self._history_service.process(observation.usage)
        return observation
