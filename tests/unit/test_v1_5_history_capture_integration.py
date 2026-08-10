from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_runtime import CapturingAccountRateLimitsReader
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoryInterval,
    HistoryReadError,
    HistoryWriteError,
)
from codexbar.application.history_runtime import HistoryService
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.reset import (
    DetailCoverage,
    ResetCreditInventory,
    ResetCreditReadResult,
)

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


def _observation(*, freshness: Freshness = Freshness.CURRENT) -> AccountRateLimitsObservation:
    usage = UsageSnapshot(
        windows=(
            UsageWindow(
                id=UsageWindowId("window_300m"),
                label="5 hours",
                remaining=Fraction(Decimal("0.70")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
        freshness=freshness,
    )
    reset = ResetCreditReadResult.current(
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=1,
            detail_coverage=DetailCoverage.COUNT_ONLY,
        )
    )
    return AccountRateLimitsObservation(usage=usage, reset_credits=reset)


class Repository:
    def __init__(self, *, fail_append: bool = False) -> None:
        self.appended: list[HistoricalSnapshot] = []
        self.fail_append = fail_append

    def append(self, snapshot: HistoricalSnapshot) -> None:
        if self.fail_append:
            raise HistoryWriteError("disk unavailable")
        self.appended.append(snapshot)

    def prune(self, cutoff: datetime) -> int:
        return 0

    def query(self, interval: HistoryInterval):
        raise HistoryReadError("unused")

    def query_window(self, window_id, interval):
        raise HistoryReadError("unused")

    def inspect(self):
        raise HistoryReadError("unused")

    def clear(self) -> None:
        raise HistoryWriteError("unused")


def test_composed_read_records_current_usage_once_without_second_read() -> None:
    observation = _observation()
    repository = Repository()

    class Reader:
        calls = 0

        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            self.calls += 1
            return observation

    reader = Reader()
    capturing = CapturingAccountRateLimitsReader(reader, HistoryService(repository))

    result = capturing.read_account_rate_limits()

    assert result is observation
    assert reader.calls == 1
    assert len(repository.appended) == 1
    assert repository.appended[0].observed_at == OBSERVED_AT


def test_stale_usage_is_excluded_from_history() -> None:
    repository = Repository()
    observation = _observation(freshness=Freshness.STALE)

    class Reader:
        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            return observation

    CapturingAccountRateLimitsReader(
        Reader(),
        HistoryService(repository),
    ).read_account_rate_limits()

    assert repository.appended == []


def test_history_failure_is_isolated_from_composed_read() -> None:
    repository = Repository(fail_append=True)
    observation = _observation()

    class Reader:
        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            return observation

    result = CapturingAccountRateLimitsReader(
        Reader(),
        HistoryService(repository),
    ).read_account_rate_limits()

    assert result is observation
