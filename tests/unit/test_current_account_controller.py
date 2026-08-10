from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.current_account import CurrentAccountController
from codexbar.domain.errors import UsageSourceUnavailableError
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
    ResetCreditReadStatus,
)
from codexbar.ui.viewmodel import UsageViewModel

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


def _observation() -> AccountRateLimitsObservation:
    usage = UsageSnapshot(
        windows=(
            UsageWindow(
                id=UsageWindowId("window_300m"),
                label="5 hours",
                remaining=Fraction(Decimal("0.80")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )
    reset = ResetCreditReadResult.current(
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=2,
            detail_coverage=DetailCoverage.COUNT_ONLY,
        )
    )
    return AccountRateLimitsObservation(usage=usage, reset_credits=reset)


def test_refresh_publishes_usage_and_reset_from_one_observation() -> None:
    observation = _observation()

    class Reader:
        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            return observation

    result = CurrentAccountController(Reader()).refresh()

    assert result is observation
    assert result.reset_credits.status is ResetCreditReadStatus.CURRENT
    assert UsageViewModel.from_snapshot(result.usage).windows[0].percent_left == 80


def test_transient_failure_keeps_only_usage_as_stale() -> None:
    observation = _observation()

    class Reader:
        calls = 0

        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            self.calls += 1
            if self.calls > 1:
                raise UsageSourceUnavailableError("offline")
            return observation

    controller = CurrentAccountController(Reader())
    first = controller.refresh()
    second = controller.refresh()

    assert first.usage.freshness is Freshness.CURRENT
    assert second.usage.freshness is Freshness.STALE
    assert second.usage.observed_at == first.usage.observed_at
    assert second.reset_credits.status is ResetCreditReadStatus.UNAVAILABLE


def test_initial_source_failure_is_not_hidden() -> None:
    class Reader:
        def read_account_rate_limits(self) -> AccountRateLimitsObservation:
            raise UsageSourceUnavailableError("offline")

    with pytest.raises(UsageSourceUnavailableError):
        CurrentAccountController(Reader()).refresh()
