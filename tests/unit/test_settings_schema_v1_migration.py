import json

from codexbar.application.settings import SettingsOrigin
from codexbar.infrastructure.settings import JsonSettingsRepository


def test_schema_1_load_migrates_in_memory_without_rewriting(tmp_path) -> None:
    env = {"HOME": str(tmp_path)}
    repository = JsonSettingsRepository(env=env)
    repository.path.parent.mkdir(parents=True)
    payload = {
        "schema_version": 1,
        "low_remaining_threshold": "0.25",
        "refresh_interval_seconds": 90,
        "notifications_enabled": False,
    }
    original = json.dumps(payload, indent=3) + "\n"
    repository.path.write_text(original)

    result = repository.load()

    assert result.origin is SettingsOrigin.PERSISTED
    assert result.source_schema_version == 1
    assert result.migrated_from_schema_v1 is True
    assert result.settings.usage_reserves.entries == ()
    assert repository.path.read_text() == original
