import json

from codexbar.application.settings import SettingsOrigin
from codexbar.infrastructure.settings import JsonSettingsRepository


def test_migration_metadata_does_not_replace_persisted_origin(tmp_path) -> None:
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

    result = repository.load()

    assert result.origin is SettingsOrigin.PERSISTED
    assert result.migrated_from_schema_v1 is True
