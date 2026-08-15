from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from codexbar.application.settings import SettingsOrigin
from codexbar.domain.errors import SettingsDocumentError
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import (
    AppSettings,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)
from codexbar.infrastructure.settings import JsonSettingsRepository


def _repository(tmp_path: Path) -> JsonSettingsRepository:
    return JsonSettingsRepository(env={"HOME": str(tmp_path)})


def _write_payload(repository: JsonSettingsRepository, payload: object) -> str:
    repository.path.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps(payload, indent=3) + "\n"
    repository.path.write_text(original, encoding="utf-8")
    return original


def _checkpoint(
    window_id: str,
    seconds: int,
    minimum: str,
) -> UsagePlanCheckpoint:
    return UsagePlanCheckpoint(
        UsageWindowId(window_id),
        TimeToReset(timedelta(seconds=seconds)),
        Fraction(Decimal(minimum)),
    )


def test_s01_defaults_save_as_canonical_schema_3(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    repository.save(AppSettings.defaults())

    payload = json.loads(repository.path.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": 3,
        "low_remaining_threshold": "0.20",
        "refresh_interval_seconds": 60,
        "notifications_enabled": True,
        "usage_reserves": {},
        "usage_plan_checkpoints": {},
        "plan_breach_notifications_enabled": False,
    }


@pytest.mark.parametrize(
    ("schema_version", "extra"),
    [
        (1, {}),
        (2, {"usage_reserves": {"opaque-weekly": "0.15"}}),
    ],
)
def test_s02_s03_legacy_load_has_plan_defaults_without_rewrite(
    tmp_path: Path,
    schema_version: int,
    extra: dict[str, object],
) -> None:
    repository = _repository(tmp_path)
    payload = {
        "schema_version": schema_version,
        "low_remaining_threshold": "0.20",
        "refresh_interval_seconds": 60,
        "notifications_enabled": True,
        **extra,
    }
    original = _write_payload(repository, payload)

    result = repository.load()

    assert result.origin is SettingsOrigin.PERSISTED
    assert result.source_schema_version == schema_version
    assert result.settings.usage_plan_checkpoints.entries == ()
    assert result.settings.plan_breach_notifications_enabled is False
    assert repository.path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("schema_version", [1, 2])
def test_s04_explicit_legacy_save_upgrades_to_schema_3(
    tmp_path: Path,
    schema_version: int,
) -> None:
    repository = _repository(tmp_path)
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "low_remaining_threshold": "0.20",
        "refresh_interval_seconds": 60,
        "notifications_enabled": True,
    }
    if schema_version == 2:
        payload["usage_reserves"] = {"opaque-weekly": "0.15"}
    _write_payload(repository, payload)

    result = repository.load()
    repository.save(result.settings)

    upgraded = json.loads(repository.path.read_text(encoding="utf-8"))
    assert upgraded["schema_version"] == 3
    assert upgraded["usage_plan_checkpoints"] == {}
    assert upgraded["plan_breach_notifications_enabled"] is False
    if schema_version == 2:
        assert upgraded["usage_reserves"] == {"opaque-weekly": "0.15"}


def test_s05_schema_3_round_trip_is_canonical_and_decimal_exact(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    alpha = UsageWindowId("alpha")
    zeta = UsageWindowId("zeta")
    settings = AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.17")),
        refresh_interval_seconds=AppSettings.defaults().refresh_interval_seconds,
        notifications_enabled=False,
        usage_reserves=UsageReservePolicy(
            (
                UsageReserve(alpha, Fraction(Decimal("0.15"))),
                UsageReserve(zeta, Fraction(Decimal("0.10"))),
            )
        ),
        usage_plan_checkpoints=UsagePlanCheckpointPolicy(
            (
                _checkpoint("zeta", 86_400, "0.30"),
                _checkpoint("alpha", 86_400, "0.40"),
                _checkpoint("alpha", 259_200, "0.55"),
            )
        ),
        plan_breach_notifications_enabled=True,
    )

    repository.save(settings)
    result = repository.load()
    payload = json.loads(repository.path.read_text(encoding="utf-8"))

    assert result.origin is SettingsOrigin.PERSISTED
    assert result.source_schema_version == 3
    assert result.settings == settings
    assert list(payload["usage_reserves"]) == ["alpha", "zeta"]
    assert list(payload["usage_plan_checkpoints"]) == ["alpha", "zeta"]
    assert payload["usage_plan_checkpoints"]["alpha"] == [
        {
            "time_to_reset_seconds": 259_200,
            "minimum_remaining": "0.55",
        },
        {
            "time_to_reset_seconds": 86_400,
            "minimum_remaining": "0.40",
        },
    ]
    assert payload["plan_breach_notifications_enabled"] is True


def test_s06_duplicate_checkpoint_coordinate_falls_back_without_rewrite(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    payload = _valid_v3_payload()
    payload["usage_plan_checkpoints"] = {
        "opaque-weekly": [
            {"time_to_reset_seconds": 259_200, "minimum_remaining": "0.55"},
            {"time_to_reset_seconds": 259_200, "minimum_remaining": "0.40"},
        ]
    }
    original = _write_payload(repository, payload)

    result = repository.load()

    assert result.settings == AppSettings.defaults()
    assert isinstance(result.diagnostic, SettingsDocumentError)
    assert "unique" in str(result.diagnostic)
    assert repository.path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("invalid_seconds", [-1, True, 1.5])
def test_s07_invalid_checkpoint_seconds_are_rejected(
    tmp_path: Path,
    invalid_seconds: object,
) -> None:
    repository = _repository(tmp_path)
    payload = _valid_v3_payload()
    payload["usage_plan_checkpoints"] = {
        "opaque-weekly": [
            {
                "time_to_reset_seconds": invalid_seconds,
                "minimum_remaining": "0.55",
            }
        ]
    }
    original = _write_payload(repository, payload)

    result = repository.load()

    assert result.settings == AppSettings.defaults()
    assert isinstance(result.diagnostic, SettingsDocumentError)
    assert "non-negative integer" in str(result.diagnostic)
    assert repository.path.read_text(encoding="utf-8") == original




def test_s07_checkpoint_seconds_outside_timedelta_range_are_rejected(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    payload = _valid_v3_payload()
    payload["usage_plan_checkpoints"] = {
        "opaque-weekly": [
            {
                "time_to_reset_seconds": 10**30,
                "minimum_remaining": "0.55",
            }
        ]
    }
    original = _write_payload(repository, payload)

    result = repository.load()

    assert result.settings == AppSettings.defaults()
    assert isinstance(result.diagnostic, SettingsDocumentError)
    assert "supported range" in str(result.diagnostic)
    assert repository.path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("invalid_minimum", [0.55, "1.01", "-0.01"])
def test_s08_invalid_checkpoint_minimum_is_rejected(
    tmp_path: Path,
    invalid_minimum: object,
) -> None:
    repository = _repository(tmp_path)
    payload = _valid_v3_payload()
    payload["usage_plan_checkpoints"] = {
        "opaque-weekly": [
            {
                "time_to_reset_seconds": 259_200,
                "minimum_remaining": invalid_minimum,
            }
        ]
    }

    result_text = _write_payload(repository, payload)
    result = repository.load()

    assert result.settings == AppSettings.defaults()
    assert isinstance(result.diagnostic, SettingsDocumentError)
    assert repository.path.read_text(encoding="utf-8") == result_text


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update({"mystery": 1}),
        lambda payload: payload.pop("usage_plan_checkpoints"),
    ],
)
def test_schema_3_keeps_exact_top_level_key_contract(
    tmp_path: Path,
    mutation,
) -> None:
    repository = _repository(tmp_path)
    payload = _valid_v3_payload()
    mutation(payload)
    original = _write_payload(repository, payload)

    result = repository.load()

    assert result.settings == AppSettings.defaults()
    assert result.diagnostic is not None
    assert repository.path.read_text(encoding="utf-8") == original


def _valid_v3_payload() -> dict[str, object]:
    return {
        "schema_version": 3,
        "low_remaining_threshold": "0.20",
        "refresh_interval_seconds": 60,
        "notifications_enabled": True,
        "usage_reserves": {},
        "usage_plan_checkpoints": {},
        "plan_breach_notifications_enabled": False,
    }
