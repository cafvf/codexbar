from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader
from codexbar.application.ports import UsageProvider
from codexbar.application.usage_adapter import AccountUsageProvider
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import DetailCoverage, ResetCreditInventory, ResetCreditReadResult

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


def _observation() -> AccountRateLimitsObservation:
    usage = UsageSnapshot(
        windows=(
            UsageWindow(
                id=UsageWindowId("window_300m"),
                label="5 hours",
                remaining=Fraction(Decimal("0.73")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.CODEX_APP_SERVER,
    )
    reset_credits = ResetCreditReadResult.current(
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=2,
            detail_coverage=DetailCoverage.COUNT_ONLY,
        )
    )
    return AccountRateLimitsObservation(usage=usage, reset_credits=reset_credits)


@dataclass
class CountingReader:
    observation: AccountRateLimitsObservation
    calls: int = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.calls += 1
        return self.observation


def test_account_usage_provider_satisfies_legacy_usage_provider_contract() -> None:
    reader = CountingReader(_observation())
    provider: UsageProvider = AccountUsageProvider(reader)

    snapshot = provider.get_usage()

    assert snapshot is reader.observation.usage
    assert reader.calls == 1


def test_get_current_usage_remains_compatible_with_account_projection() -> None:
    reader: AccountRateLimitsReader = CountingReader(_observation())
    provider = AccountUsageProvider(reader)

    snapshot = GetCurrentUsage(provider).execute()

    assert snapshot.windows[0].remaining == Fraction(Decimal("0.73"))


def test_each_legacy_get_usage_call_performs_exactly_one_composed_read() -> None:
    reader = CountingReader(_observation())
    provider = AccountUsageProvider(reader)

    first = provider.get_usage()
    second = provider.get_usage()

    assert first is reader.observation.usage
    assert second is reader.observation.usage
    assert reader.calls == 2


def test_adapter_does_not_expose_reset_state_through_usage_snapshot() -> None:
    reader = CountingReader(_observation())

    snapshot = AccountUsageProvider(reader).get_usage()

    assert snapshot is reader.observation.usage
    assert not hasattr(snapshot, "reset_credits")
