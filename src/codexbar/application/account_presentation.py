from __future__ import annotations

from threading import RLock

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.application.revisions import CurrentRevision
from codexbar.domain.errors import UsageError
from codexbar.domain.models import Freshness
from codexbar.domain.reset import ResetCreditReadResult


class LatestAccountObservationReader:
    """Capture one coherent account observation for all Current-derived surfaces."""

    def __init__(self, reader: AccountRateLimitsReader) -> None:
        self._reader = reader
        self._latest: AccountRateLimitsObservation | None = None
        self._current_revision = CurrentRevision()
        self._lock = RLock()

    @property
    def latest(self) -> AccountRateLimitsObservation | None:
        return self.capture()[0]

    @property
    def current_revision(self) -> CurrentRevision:
        return self.capture()[1]

    def capture(self) -> tuple[AccountRateLimitsObservation | None, CurrentRevision]:
        """Atomically capture Current observation and its matching runtime revision."""
        with self._lock:
            return self._latest, self._current_revision

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        try:
            observation = self._reader.read_account_rate_limits()
        except UsageError:
            self._mark_latest_stale()
            raise
        with self._lock:
            self._latest = observation
            if observation.usage.freshness is Freshness.CURRENT:
                self._current_revision = self._current_revision.next()
        return observation

    def _mark_latest_stale(self) -> None:
        with self._lock:
            latest = self._latest
            if latest is None:
                return
            self._latest = AccountRateLimitsObservation(
                usage=latest.usage.as_stale(),
                reset_credits=ResetCreditReadResult.unavailable(
                    "account read failed; reset current state is unavailable"
                ),
            )
