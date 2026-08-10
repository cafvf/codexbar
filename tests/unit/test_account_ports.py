from datetime import UTC, datetime
from decimal import Decimal
from typing import get_type_hints

from codexbar.application.account import (
    AccountRateLimitsObservation,
    AccountRateLimitsReader,
    ResetCreditConsumer,
)
from codexbar.application.ports import UsageProvider
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import DetailCoverage, ResetCreditInventory, ResetCreditReadResult

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


def _usage() -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                id=UsageWindowId("window_10080m"),
                label="Weekly",
                remaining=Fraction(Decimal("0.42")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )


def _reset_result() -> ResetCreditReadResult:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=2,
        detail_coverage=DetailCoverage.COUNT_ONLY,
    )
    return ResetCreditReadResult.current(inventory)


def test_account_observation_keeps_usage_and_reset_current_separate() -> None:
    usage = _usage()
    reset_credits = _reset_result()

    observation = AccountRateLimitsObservation(usage=usage, reset_credits=reset_credits)

    assert observation.usage is usage
    assert observation.reset_credits is reset_credits


def test_account_reader_exposes_one_composed_read_contract() -> None:
    observation = AccountRateLimitsObservation(usage=_usage(), reset_credits=_reset_result())

    class FakeReader:
        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            return observation

    reader: AccountRateLimitsReader = FakeReader()

    assert reader.read_account_rate_limits() is observation


def test_existing_usage_provider_contract_remains_unchanged() -> None:
    usage = _usage()

    class FakeUsageProvider:
        def get_usage(self) -> UsageSnapshot:
            return usage

    provider: UsageProvider = FakeUsageProvider()

    assert provider.get_usage() is usage
    assert get_type_hints(UsageProvider.get_usage)["return"] is UsageSnapshot


def test_reader_and_consumer_are_distinct_application_ports() -> None:
    assert AccountRateLimitsReader is not ResetCreditConsumer
    assert "read_account_rate_limits" in AccountRateLimitsReader.__dict__
    assert "read_account_rate_limits" not in ResetCreditConsumer.__dict__
