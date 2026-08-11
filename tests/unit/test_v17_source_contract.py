from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from codexbar.domain.errors import UsageSchemaError
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.infrastructure.app_server import JsonObject, parse_rate_limits_response

FIXTURES = Path(__file__).parents[1] / "fixtures"
OBSERVED_AT = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


def fixture(name: str) -> JsonObject:
    value: Any = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def test_tv_1710_legacy_rate_limits_remain_readable() -> None:
    snapshot = parse_rate_limits_response(
        fixture("v17_rate_limits_legacy.json"),
        observed_at=OBSERVED_AT,
    )

    assert len(snapshot.windows) == 1
    assert snapshot.windows[0].id == UsageWindowId("window_300m")
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.75"))


def test_tv_1709_explicit_codex_bucket_wins_over_legacy_and_unrelated_bucket() -> None:
    snapshot = parse_rate_limits_response(
        fixture("v17_rate_limits_multi_bucket_codex.json"),
        observed_at=OBSERVED_AT,
    )

    assert [window.id for window in snapshot.windows] == [UsageWindowId("window_720m")]
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.75"))
    assert all(window.id != UsageWindowId("window_1440m") for window in snapshot.windows)


def test_unrelated_multi_bucket_does_not_merge_and_legacy_remains_authoritative() -> None:
    snapshot = parse_rate_limits_response(
        fixture("v17_rate_limits_unrelated_only.json"),
        observed_at=OBSERVED_AT,
    )

    assert [window.id for window in snapshot.windows] == [UsageWindowId("window_300m")]
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.60"))


def test_malformed_explicit_codex_bucket_falls_back_to_valid_legacy_snapshot() -> None:
    snapshot = parse_rate_limits_response(
        fixture("v17_rate_limits_malformed_codex_fallback.json"),
        observed_at=OBSERVED_AT,
    )

    assert [window.id for window in snapshot.windows] == [UsageWindowId("window_300m")]
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.65"))


def test_tv_1711_dynamic_720_minute_window_remains_dynamic() -> None:
    snapshot = parse_rate_limits_response(
        fixture("v17_rate_limits_dynamic_720.json"),
        observed_at=OBSERVED_AT,
    )

    assert len(snapshot.windows) == 1
    assert snapshot.windows[0].id == UsageWindowId("window_720m")
    assert snapshot.windows[0].label == "12 hours"
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.60"))


def test_malformed_codex_without_legacy_fails_safely() -> None:
    payload: JsonObject = {
        "id": 1,
        "result": {
            "rateLimitsByLimitId": {
                "codex": {
                    "primary": {
                        "usedPercent": "invalid",
                        "windowDurationMins": 720,
                        "resetsAt": None,
                    }
                }
            }
        },
    }

    with pytest.raises(UsageSchemaError, match="numeric"):
        parse_rate_limits_response(payload, observed_at=OBSERVED_AT)
