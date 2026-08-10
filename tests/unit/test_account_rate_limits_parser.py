from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.domain.errors import UsageSchemaError
from codexbar.domain.models import Fraction
from codexbar.domain.reset import DetailCoverage, ExpiryKind, ResetCreditReadStatus
from codexbar.infrastructure.account_rate_limits import parse_account_rate_limits_response

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)


def _parse(fixture_json, name: str):
    return parse_account_rate_limits_response(fixture_json(name), observed_at=OBSERVED_AT)


def test_capability_null_keeps_usage_current_and_reset_unavailable(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_null.json")

    assert observation.usage.windows[0].remaining == Fraction(Decimal("0.90"))
    assert observation.reset_credits.status is ResetCreditReadStatus.UNAVAILABLE
    assert observation.reset_credits.inventory is None


def test_count_only_preserves_authoritative_count(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_count_only.json")
    inventory = observation.reset_credits.inventory

    assert observation.reset_credits.status is ResetCreditReadStatus.CURRENT
    assert inventory is not None
    assert inventory.observed_at == OBSERVED_AT
    assert inventory.available_count == 3
    assert inventory.detail_coverage is DetailCoverage.COUNT_ONLY
    assert inventory.credits == ()


def test_partial_details_are_classified_from_unique_returned_rows(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_partial.json")
    inventory = observation.reset_credits.inventory

    assert inventory is not None
    assert inventory.available_count == 4
    assert inventory.detail_coverage is DetailCoverage.DETAILS_PARTIAL
    assert [credit.credit_id.value for credit in inventory.credits] == ["credit-A", "credit-B"]


def test_complete_details_preserve_expiring_and_non_expiring_semantics(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_complete.json")
    inventory = observation.reset_credits.inventory

    assert inventory is not None
    assert inventory.detail_coverage is DetailCoverage.DETAILS_COMPLETE
    assert inventory.credits[0].expiry.kind is ExpiryKind.EXPIRES_AT
    assert inventory.credits[0].expiry.instant == datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    assert inventory.credits[1].expiry.kind is ExpiryKind.DOES_NOT_EXPIRE
    assert inventory.credits[1].expiry.instant is None
    assert inventory.credits[0].granted_at == datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def test_future_enum_strings_are_preserved_without_corrupting_usage(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_future_enums.json")
    inventory = observation.reset_credits.inventory

    assert observation.usage.windows[0].remaining.percent == Decimal("90")
    assert inventory is not None
    assert inventory.credits[0].reset_type == "futureResetType"
    assert inventory.credits[0].status == "futureStatus"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "account_rate_limits_reset_duplicate_ids.json",
        "account_rate_limits_reset_details_over_count.json",
        "account_rate_limits_reset_malformed_detail.json",
    ],
)
def test_malformed_reset_subtree_degrades_reset_only(fixture_json, fixture_name: str) -> None:
    observation = _parse(fixture_json, fixture_name)

    assert observation.usage.windows[0].remaining.percent == Decimal("90")
    assert observation.reset_credits.status is ResetCreditReadStatus.UNAVAILABLE
    assert observation.reset_credits.inventory is None
    assert observation.reset_credits.diagnostic is not None


def test_duplicate_ids_are_not_silently_deduplicated(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_duplicate_ids.json")

    assert observation.reset_credits.diagnostic is not None
    assert "unique" in observation.reset_credits.diagnostic


def test_detail_count_above_authoritative_count_is_rejected(fixture_json) -> None:
    observation = _parse(fixture_json, "account_rate_limits_reset_details_over_count.json")

    assert observation.reset_credits.diagnostic is not None
    assert "availableCount" in observation.reset_credits.diagnostic


def test_invalid_usage_still_fails_even_when_reset_subtree_is_valid(fixture_json) -> None:
    payload = fixture_json("account_rate_limits_reset_count_only.json")
    payload["result"]["rateLimits"]["primary"].pop("windowDurationMins")

    with pytest.raises(UsageSchemaError):
        parse_account_rate_limits_response(payload, observed_at=OBSERVED_AT)


def test_observed_at_must_remain_timezone_aware(fixture_json) -> None:
    payload = fixture_json("account_rate_limits_reset_count_only.json")

    with pytest.raises(ValueError, match="observed_at"):
        parse_account_rate_limits_response(
            payload,
            observed_at=datetime(2026, 8, 10, 15, 0),
        )
