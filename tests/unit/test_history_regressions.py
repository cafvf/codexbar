from __future__ import annotations

import json
from decimal import Decimal

from codexbar.application.history import HistoricalSnapshot
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.settings import (
    DEFAULT_NOTIFICATIONS_ENABLED,
    MAX_REFRESH_INTERVAL_SECONDS,
    MIN_REFRESH_INTERVAL_SECONDS,
    AppSettings,
)
from codexbar.infrastructure.settings import JsonSettingsRepository

SETTINGS_KEYS = {
    "schema_version",
    "low_remaining_threshold",
    "refresh_interval_seconds",
    "notifications_enabled",
}


def test_regression_v1_1_settings_schema_remains_version_1_without_history_fields(
    tmp_path,
) -> None:
    repository = JsonSettingsRepository(
        env={
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        }
    )
    repository.save(AppSettings.defaults())

    payload = json.loads(repository.path.read_text(encoding="utf-8"))

    assert set(payload) == SETTINGS_KEYS
    assert payload["schema_version"] == 1
    assert not any("history" in key for key in payload)


def test_regression_v1_1_settings_defaults_are_unchanged() -> None:
    settings = AppSettings.defaults()

    assert settings.low_remaining_threshold == Fraction(Decimal("0.20"))
    assert settings.refresh_interval_seconds.value == 60
    assert settings.notifications_enabled is DEFAULT_NOTIFICATIONS_ENABLED
    assert MIN_REFRESH_INTERVAL_SECONDS == 10
    assert MAX_REFRESH_INTERVAL_SECONDS == 3600


def test_regression_v1_1_usage_policy_still_comes_from_settings_threshold() -> None:
    settings = AppSettings.defaults()

    assert (
        settings.usage_policy().low_remaining_threshold
        == settings.low_remaining_threshold
    )


def test_regression_v1_0_usage_snapshot_freshness_contract_is_unchanged() -> None:
    current = UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.50")),
            ),
        ),
        observed_at=__import__("datetime").datetime(
            2026,
            8,
            9,
            12,
            0,
            tzinfo=__import__("datetime").UTC,
        ),
        source=UsageSource.MOCK,
    )

    stale = current.as_stale()

    assert current.freshness is Freshness.CURRENT
    assert stale.freshness is Freshness.STALE
    assert stale.windows == current.windows
    assert stale.observed_at == current.observed_at
    assert stale.source == current.source


def test_regression_v1_3_history_projection_does_not_mutate_current_snapshot() -> None:
    snapshot = UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.50")),
            ),
        ),
        observed_at=__import__("datetime").datetime(
            2026,
            8,
            9,
            12,
            0,
            tzinfo=__import__("datetime").UTC,
        ),
        source=UsageSource.MOCK,
    )

    historical = HistoricalSnapshot.from_usage_snapshot(snapshot)

    assert snapshot.freshness is Freshness.CURRENT
    assert historical.observed_at == snapshot.observed_at
    assert historical.source == snapshot.source
    assert historical.windows[0].window_id == snapshot.windows[0].id
