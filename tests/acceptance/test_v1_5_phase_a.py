from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account_operations import (
    AccountOperationCoordinator,
    CoordinatedAccountRateLimitsReader,
)
from codexbar.application.account_runtime import CapturingAccountRateLimitsReader
from codexbar.application.history import HistoricalSnapshot, HistoryReadError, HistoryWriteError
from codexbar.application.history_runtime import HistoryService
from codexbar.application.ports import UsageProvider
from codexbar.application.usage_adapter import AccountUsageProvider
from codexbar.domain.reset import ResetCreditReadStatus
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


class Gateway:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def call(self, method: str, *, request_id: int = 1, params=None):
        self.calls += 1
        return self.payload


class Repository:
    def __init__(self):
        self.appended: list[HistoricalSnapshot] = []

    def append(self, snapshot: HistoricalSnapshot) -> None:
        self.appended.append(snapshot)

    def prune(self, cutoff: datetime) -> int:
        return 0

    def query(self, interval):
        raise HistoryReadError("unused")

    def query_window(self, window_id, interval):
        raise HistoryReadError("unused")

    def inspect(self):
        raise HistoryReadError("unused")

    def clear(self) -> None:
        raise HistoryWriteError("unused")


def test_phase_a_one_read_produces_composed_state_and_legacy_usage(fixture_json) -> None:
    gateway = Gateway(fixture_json("account_rate_limits_reset_complete.json"))
    repository = Repository()
    coordinator = AccountOperationCoordinator()
    reader = CodexAccountRateLimitsReader(gateway, clock=lambda: OBSERVED_AT)
    reader = CapturingAccountRateLimitsReader(reader, HistoryService(repository))
    reader = CoordinatedAccountRateLimitsReader(reader, coordinator)

    observation = reader.read_account_rate_limits()
    provider: UsageProvider = AccountUsageProvider(reader)

    assert gateway.calls == 1
    assert observation.usage.windows[0].remaining.percent == Decimal("90")
    assert observation.reset_credits.status is ResetCreditReadStatus.CURRENT
    assert len(repository.appended) == 1

    snapshot = provider.get_usage()

    assert gateway.calls == 2
    assert snapshot.windows[0].remaining.percent == Decimal("90")
    assert len(repository.appended) == 2
