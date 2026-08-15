from datetime import UTC, datetime

import pytest

from codexbar.domain.errors import UsageSchemaError
from codexbar.infrastructure.app_server import parse_rate_limits_response

NOW = datetime(2026, 8, 8, tzinfo=UTC)


@pytest.mark.parametrize(
    "primary",
    [
        {"usedPercent": -1, "windowDurationMins": 300},
        {"usedPercent": 101, "windowDurationMins": 300},
        {"usedPercent": "NaN", "windowDurationMins": 300},
        {"usedPercent": 10, "windowDurationMins": 0},
        {"usedPercent": 10, "windowDurationMins": "300"},
        {"usedPercent": 10, "windowDurationMins": 300, "resetsAt": "tomorrow"},
    ],
)
def test_invalid_window_schema_fails_closed(primary) -> None:
    payload = {"result": {"rateLimits": {"primary": primary, "secondary": None}}}
    with pytest.raises(UsageSchemaError):
        parse_rate_limits_response(payload, observed_at=NOW)


def test_empty_but_valid_rate_limits_snapshot_is_preserved() -> None:
    payload = {
        "result": {
            "rateLimits": {
                "primary": None,
                "secondary": None,
                "rateLimitReachedType": None,
            }
        }
    }
    snapshot = parse_rate_limits_response(payload, observed_at=NOW)
    assert snapshot.windows == ()


def test_duplicate_normalized_window_ids_fail_as_schema_error() -> None:
    payload = {
        "result": {
            "rateLimits": {
                "primary": {"usedPercent": 10, "windowDurationMins": 300},
                "secondary": {"usedPercent": 20, "windowDurationMins": 300},
            }
        }
    }

    with pytest.raises(UsageSchemaError, match="unique identities"):
        parse_rate_limits_response(payload, observed_at=NOW)
