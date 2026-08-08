from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import UsageSchemaError, UsageSourceUnavailableError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.app_server import parse_rate_limits_response
from codexbar.ui.viewmodel import UsageViewModel

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


def test_ac_usage_001_used_percent_is_normalized_to_remaining_fraction(fixture_json) -> None:
    snapshot = parse_rate_limits_response(
        fixture_json("rate_limits_two_windows.json"), observed_at=OBSERVED_AT
    )
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.75"))


def test_ac_usage_002_all_reported_windows_are_preserved(fixture_json) -> None:
    snapshot = parse_rate_limits_response(
        fixture_json("rate_limits_two_windows.json"), observed_at=OBSERVED_AT
    )
    assert [(w.id.value, w.label) for w in snapshot.windows] == [
        ("window_300m", "5 hours"),
        ("window_10080m", "Weekly"),
    ]


def test_ac_usage_003_missing_window_is_not_synthesized_as_zero(fixture_json) -> None:
    snapshot = parse_rate_limits_response(
        fixture_json("rate_limits_weekly_only.json"), observed_at=OBSERVED_AT
    )
    assert len(snapshot.windows) == 1
    assert snapshot.windows[0].id == UsageWindowId("window_10080m")
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.59"))


@pytest.mark.parametrize("value", [Decimal("-0.01"), Decimal("1.01"), Decimal("NaN")])
def test_ac_usage_004_fraction_rejects_invalid_domain_values(value: Decimal) -> None:
    with pytest.raises(ValueError):
        Fraction(value)


def test_ac_usage_005_reset_timestamps_are_timezone_aware(fixture_json) -> None:
    snapshot = parse_rate_limits_response(
        fixture_json("rate_limits_two_windows.json"), observed_at=OBSERVED_AT
    )
    assert all(
        w.resets_at is not None and w.resets_at.utcoffset() is not None
        for w in snapshot.windows
    )


def test_ac_usage_006_source_failure_is_exposed_as_typed_error() -> None:
    class FailingProvider:
        def get_usage(self) -> UsageSnapshot:
            raise UsageSourceUnavailableError("offline")

    with pytest.raises(UsageSourceUnavailableError):
        GetCurrentUsage(FailingProvider()).execute()


def test_ac_usage_007_unknown_schema_fails_closed() -> None:
    malformed = {"id": 1, "result": {"rateLimits": {"primary": {"usedPercent": 20}}}}
    with pytest.raises(UsageSchemaError):
        parse_rate_limits_response(malformed, observed_at=OBSERVED_AT)


def test_ac_usage_008_zero_remaining_is_presented_as_exhausted() -> None:
    snapshot = UsageSnapshot(
        windows=(UsageWindow(UsageWindowId("weekly"), "Weekly", Fraction(Decimal("0"))),),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )
    state = UsageViewModel.from_snapshot(snapshot)
    assert state.windows[0].percent_left == 0
    assert state.windows[0].state.value == "exhausted"


def test_ac_usage_010_transient_failure_returns_last_snapshot_as_stale() -> None:
    class SucceedsThenFails:
        def __init__(self) -> None:
            self.calls = 0

        def get_usage(self) -> UsageSnapshot:
            self.calls += 1
            if self.calls > 1:
                raise UsageSourceUnavailableError("offline")
            return UsageSnapshot((), OBSERVED_AT, UsageSource.MOCK)

    coordinator = RefreshCoordinator(GetCurrentUsage(SucceedsThenFails()))
    first = coordinator.refresh()
    second = coordinator.refresh()
    assert second.observed_at == first.observed_at
    assert second.freshness is Freshness.STALE
