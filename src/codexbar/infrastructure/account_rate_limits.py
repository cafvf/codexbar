from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import cast

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.domain.errors import UsageSchemaError
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
    ResetCreditReadResult,
)
from codexbar.infrastructure.app_server import JsonObject, parse_rate_limits_response


def parse_account_rate_limits_response(
    message: JsonObject,
    *,
    observed_at: datetime,
) -> AccountRateLimitsObservation:
    """Normalize one account/rateLimits/read response into usage plus reset-current state."""
    usage = parse_rate_limits_response(message, observed_at=observed_at)
    reset_credits = _parse_reset_credits_safely(message, observed_at=observed_at)
    return AccountRateLimitsObservation(usage=usage, reset_credits=reset_credits)


def _parse_reset_credits_safely(
    message: JsonObject,
    *,
    observed_at: datetime,
) -> ResetCreditReadResult:
    try:
        result = _mapping(message.get("result"), "result")
        raw_summary = result.get("rateLimitResetCredits")
        if raw_summary is None:
            return ResetCreditReadResult.unavailable("reset credit capability not provided")

        summary = _mapping(raw_summary, "result.rateLimitResetCredits")
        inventory = _parse_reset_inventory(summary, observed_at=observed_at)
        return ResetCreditReadResult.current(inventory)
    except (UsageSchemaError, ValueError) as exc:
        return ResetCreditReadResult.unavailable(f"invalid reset credit data: {exc}")


def _parse_reset_inventory(
    summary: JsonObject,
    *,
    observed_at: datetime,
) -> ResetCreditInventory:
    available_count = _non_negative_int(summary.get("availableCount"), "availableCount")
    raw_credits = summary.get("credits")

    if raw_credits is None:
        return ResetCreditInventory(
            observed_at=observed_at,
            available_count=available_count,
            detail_coverage=DetailCoverage.COUNT_ONLY,
        )

    if not isinstance(raw_credits, list):
        raise UsageSchemaError("credits must be an array or null")

    credits = tuple(
        _parse_reset_credit(_mapping(raw, f"credits[{index}]"))
        for index, raw in enumerate(raw_credits)
    )
    detail_count = len(credits)
    if detail_count > available_count:
        raise UsageSchemaError("credit detail count exceeds availableCount")

    coverage = (
        DetailCoverage.DETAILS_COMPLETE
        if detail_count == available_count
        else DetailCoverage.DETAILS_PARTIAL
    )
    return ResetCreditInventory(
        observed_at=observed_at,
        available_count=available_count,
        detail_coverage=coverage,
        credits=credits,
    )


def _parse_reset_credit(raw: JsonObject) -> ResetCreditDetail:
    credit_id = ResetCreditId(_required_string(raw.get("id"), "credit.id"))
    reset_type = _required_string(raw.get("resetType"), "credit.resetType")
    status = _required_string(raw.get("status"), "credit.status")
    granted_at = _unix_timestamp(raw.get("grantedAt"), "credit.grantedAt")

    expires_raw = raw.get("expiresAt")
    expiry = (
        ExpiryKnowledge.does_not_expire()
        if expires_raw is None
        else ExpiryKnowledge.expires_at(_unix_timestamp(expires_raw, "credit.expiresAt"))
    )

    return ResetCreditDetail(
        credit_id=credit_id,
        reset_type=reset_type,
        status=status,
        granted_at=granted_at,
        expiry=expiry,
        title=_optional_string(raw.get("title"), "credit.title"),
        description=_optional_string(raw.get("description"), "credit.description"),
    )


def _mapping(value: object, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise UsageSchemaError(f"{path} must be an object")
    return cast(JsonObject, value)


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise UsageSchemaError(f"{field} must be a non-negative integer")
    return value


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UsageSchemaError(f"{field} must be a non-empty string")
    return value


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise UsageSchemaError(f"{field} must be a string or null")
    return value


def _unix_timestamp(value: object, field: str) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UsageSchemaError(f"{field} must be a Unix timestamp")
    if not math.isfinite(value):
        raise UsageSchemaError(f"{field} must be finite")
    try:
        return datetime.fromtimestamp(value, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise UsageSchemaError(f"{field} is outside the supported datetime range") from exc
