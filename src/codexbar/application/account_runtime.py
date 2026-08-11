from __future__ import annotations

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.application.history_runtime import HistoryService
from codexbar.application.reset_ledger_service import ResetLedgerService


class CapturingAccountRateLimitsReader:
    """Capture optional local evidence from the same authoritative account read."""

    def __init__(
        self,
        reader: AccountRateLimitsReader,
        history_service: HistoryService | None,
        reset_ledger_service: ResetLedgerService | None = None,
    ) -> None:
        self._reader = reader
        self._history_service = history_service
        self._reset_ledger_service = reset_ledger_service

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        observation = self._reader.read_account_rate_limits()
        if self._history_service is not None:
            self._history_service.process(observation.usage)
        if self._reset_ledger_service is not None:
            self._reset_ledger_service.process(observation.reset_credits)
        return observation
