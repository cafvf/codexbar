from datetime import UTC, datetime
from decimal import Decimal

from codexbar.domain.reset import ResetCreditReadStatus
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


class Gateway:
    def __init__(self, payload):
        self.payload = payload
        self.calls: list[str] = []

    def call(self, method: str, *, request_id: int = 1, params=None):
        self.calls.append(method)
        return self.payload


def test_reader_uses_one_gateway_call_for_usage_and_reset(fixture_json) -> None:
    gateway = Gateway(fixture_json("account_rate_limits_reset_count_only.json"))
    reader = CodexAccountRateLimitsReader(gateway, clock=lambda: OBSERVED_AT)

    observation = reader.read_account_rate_limits()

    assert gateway.calls == ["account/rateLimits/read"]
    assert observation.usage.windows[0].remaining.percent == Decimal("90")
    assert observation.reset_credits.status is ResetCreditReadStatus.CURRENT
    assert observation.reset_credits.inventory is not None
    assert observation.reset_credits.inventory.available_count == 3
