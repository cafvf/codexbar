import json
from decimal import Decimal

from codexbar.application.settings import SettingsOrigin
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import AppSettings
from codexbar.infrastructure.settings import JsonSettingsRepository


def test_explicit_save_writes_canonical_schema_2_and_round_trips(tmp_path) -> None:
    repository = JsonSettingsRepository(env={"HOME": str(tmp_path)})
    settings = AppSettings.defaults().with_usage_reserve(
        UsageWindowId("window_10080m"),
        Fraction(Decimal("0.15")),
    )

    repository.save(settings)

    payload = json.loads(repository.path.read_text())
    assert payload["schema_version"] == 2
    assert payload["usage_reserves"] == {"window_10080m": "0.15"}

    loaded = repository.load()
    assert loaded.origin is SettingsOrigin.PERSISTED
    assert loaded.source_schema_version == 2
    assert loaded.settings == settings


def test_next_save_after_schema_1_load_upgrades_only_on_explicit_save(tmp_path) -> None:
    repository = JsonSettingsRepository(env={"HOME": str(tmp_path)})
    repository.path.parent.mkdir(parents=True)
    repository.path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "low_remaining_threshold": "0.20",
                "refresh_interval_seconds": 60,
                "notifications_enabled": True,
            }
        )
    )

    loaded = repository.load()
    assert json.loads(repository.path.read_text())["schema_version"] == 1

    repository.save(loaded.settings)

    assert json.loads(repository.path.read_text())["schema_version"] == 2
