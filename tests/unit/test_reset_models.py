from datetime import UTC, datetime, timedelta, timezone

import pytest

from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKind,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
    ResetCreditReadResult,
    ResetCreditReadStatus,
)

OBSERVED_AT = datetime(2026, 8, 10, 15, 0, tzinfo=UTC)
GRANTED_AT = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
EXPIRES_AT = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


def _detail(
    credit_id: str = "credit-A",
    *,
    expiry: ExpiryKnowledge | None = None,
) -> ResetCreditDetail:
    return ResetCreditDetail(
        credit_id=ResetCreditId(credit_id),
        reset_type="codexRateLimits",
        status="available",
        granted_at=GRANTED_AT,
        expiry=expiry or ExpiryKnowledge.expires_at(EXPIRES_AT),
        title="Reset credit",
        description="Earned reset",
    )


def test_ac_reset_004_available_count_accepts_non_negative_integer_boundaries() -> None:
    zero = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=0,
        detail_coverage=DetailCoverage.DETAILS_COMPLETE,
    )
    positive = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=2,
        detail_coverage=DetailCoverage.COUNT_ONLY,
    )

    assert zero.available_count == 0
    assert positive.available_count == 2


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_ac_reset_004_available_count_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError, match="available_count"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=value,  # type: ignore[arg-type]
            detail_coverage=DetailCoverage.COUNT_ONLY,
        )


def test_ac_reset_005_unavailable_is_distinct_from_zero_available_inventory() -> None:
    zero_inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=0,
        detail_coverage=DetailCoverage.DETAILS_COMPLETE,
    )

    current_zero = ResetCreditReadResult.current(zero_inventory)
    unavailable = ResetCreditReadResult.unavailable()

    assert current_zero.status is ResetCreditReadStatus.CURRENT
    assert current_zero.inventory is zero_inventory
    assert unavailable.status is ResetCreditReadStatus.UNAVAILABLE
    assert unavailable.inventory is None


def test_ac_reset_006_count_only_has_authoritative_count_without_details() -> None:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=3,
        detail_coverage=DetailCoverage.COUNT_ONLY,
    )

    assert inventory.available_count == 3
    assert inventory.credits == ()


def test_ac_reset_007_partial_requires_fewer_details_than_authoritative_count() -> None:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=3,
        detail_coverage=DetailCoverage.DETAILS_PARTIAL,
        credits=(_detail(),),
    )

    assert len(inventory.credits) == 1


@pytest.mark.parametrize(
    ("available_count", "credits"),
    [(0, ()), (2, (_detail("A"), _detail("B")))],
)
def test_ac_reset_008_complete_requires_exact_detail_coverage(
    available_count: int,
    credits: tuple[ResetCreditDetail, ...],
) -> None:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=available_count,
        detail_coverage=DetailCoverage.DETAILS_COMPLETE,
        credits=credits,
    )

    assert len(inventory.credits) == inventory.available_count


def test_ac_reset_009_detail_count_above_authoritative_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="detail count"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=1,
            detail_coverage=DetailCoverage.DETAILS_COMPLETE,
            credits=(_detail("A"), _detail("B")),
        )


def test_ac_reset_010_duplicate_credit_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=2,
            detail_coverage=DetailCoverage.DETAILS_COMPLETE,
            credits=(_detail("same"), _detail("same")),
        )


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_ac_reset_011_credit_id_must_be_non_blank(value: str) -> None:
    with pytest.raises(ValueError, match="id"):
        ResetCreditId(value)


def test_ac_reset_011_credit_id_remains_opaque() -> None:
    credit_id = ResetCreditId("  backend::opaque/id  ")

    assert credit_id.value == "  backend::opaque/id  "


def test_ac_reset_012_granted_at_is_required_to_be_aware_and_normalized_to_utc() -> None:
    local_tz = timezone(timedelta(hours=-3))
    detail = ResetCreditDetail(
        credit_id=ResetCreditId("A"),
        reset_type="future-reset-type",
        status="future-status",
        granted_at=datetime(2026, 8, 9, 9, 0, tzinfo=local_tz),
        expiry=ExpiryKnowledge.does_not_expire(),
    )

    assert detail.granted_at == GRANTED_AT
    assert detail.granted_at.tzinfo is UTC

    with pytest.raises(ValueError, match="granted_at"):
        ResetCreditDetail(
            credit_id=ResetCreditId("B"),
            reset_type="codexRateLimits",
            status="available",
            granted_at=datetime(2026, 8, 9, 12, 0),
            expiry=ExpiryKnowledge.does_not_expire(),
        )


def test_ac_reset_013_concrete_expiry_is_explicit_and_normalized_to_utc() -> None:
    local_tz = timezone(timedelta(hours=-3))
    expiry = ExpiryKnowledge.expires_at(datetime(2026, 8, 11, 9, 0, tzinfo=local_tz))

    assert expiry.kind is ExpiryKind.EXPIRES_AT
    assert expiry.instant == EXPIRES_AT
    assert expiry.instant is not None
    assert expiry.instant.tzinfo is UTC


def test_ac_reset_014_null_source_semantics_have_explicit_non_expiring_value() -> None:
    expiry = ExpiryKnowledge.does_not_expire()
    detail = _detail(expiry=expiry)

    assert detail.expiry.kind is ExpiryKind.DOES_NOT_EXPIRE
    assert detail.expiry.instant is None


def test_ac_reset_015_unknown_expiry_is_not_valid_for_a_detailed_credit() -> None:
    with pytest.raises(ValueError, match="expiry must be known"):
        _detail(expiry=ExpiryKnowledge.unknown())


def test_expiry_knowledge_rejects_naive_concrete_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ExpiryKnowledge.expires_at(datetime(2026, 8, 11, 12, 0))


def test_inventory_rejects_inconsistent_coverage_classifications() -> None:
    with pytest.raises(ValueError, match="COUNT_ONLY"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=1,
            detail_coverage=DetailCoverage.COUNT_ONLY,
            credits=(_detail(),),
        )

    with pytest.raises(ValueError, match="DETAILS_PARTIAL"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=1,
            detail_coverage=DetailCoverage.DETAILS_PARTIAL,
            credits=(_detail(),),
        )

    with pytest.raises(ValueError, match="DETAILS_COMPLETE"):
        ResetCreditInventory(
            observed_at=OBSERVED_AT,
            available_count=2,
            detail_coverage=DetailCoverage.DETAILS_COMPLETE,
            credits=(_detail(),),
        )


def test_inventory_observed_at_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        ResetCreditInventory(
            observed_at=datetime(2026, 8, 10, 15, 0),
            available_count=0,
            detail_coverage=DetailCoverage.DETAILS_COMPLETE,
        )


def test_reset_credit_read_result_distinguishes_current_from_unavailable() -> None:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=0,
        detail_coverage=DetailCoverage.DETAILS_COMPLETE,
    )

    current = ResetCreditReadResult.current(inventory)
    unavailable = ResetCreditReadResult.unavailable("reset capability not provided")

    assert current.status is ResetCreditReadStatus.CURRENT
    assert current.inventory is inventory
    assert current.diagnostic is None
    assert unavailable.status is ResetCreditReadStatus.UNAVAILABLE
    assert unavailable.inventory is None
    assert unavailable.diagnostic == "reset capability not provided"


def test_reset_credit_read_result_rejects_contradictory_state() -> None:
    inventory = ResetCreditInventory(
        observed_at=OBSERVED_AT,
        available_count=0,
        detail_coverage=DetailCoverage.DETAILS_COMPLETE,
    )

    with pytest.raises(ValueError, match="CURRENT"):
        ResetCreditReadResult(status=ResetCreditReadStatus.CURRENT)
    with pytest.raises(ValueError, match="UNAVAILABLE"):
        ResetCreditReadResult(
            status=ResetCreditReadStatus.UNAVAILABLE,
            inventory=inventory,
        )


def test_ac_reset_020_domain_models_contain_only_normalized_values() -> None:
    fields = ResetCreditDetail.__dataclass_fields__

    assert "raw_payload" not in fields
    assert "account_id" not in fields
    assert "credentials" not in fields
