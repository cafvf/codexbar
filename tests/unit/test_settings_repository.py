import json
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest

from codexbar.domain.errors import SettingsWriteError
from codexbar.domain.models import Fraction


def _modules():
    domain = import_module("codexbar.domain.settings")
    infrastructure = import_module("codexbar.infrastructure.settings")
    return domain, infrastructure


def _custom_settings(domain):
    return domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(120),
        notifications_enabled=False,
    )


def test_missing_file_returns_defaults_without_creating_file(tmp_path: Path) -> None:
    domain, infrastructure = _modules()
    env = {"HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)

    result = repository.load()

    assert result.settings == domain.AppSettings.defaults()
    assert result.origin.value == "defaults"
    assert not (tmp_path / "config/codexbar/settings.json").exists()


def test_valid_document_round_trips_without_float_conversion(tmp_path: Path) -> None:
    domain, infrastructure = _modules()
    env = {"HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)
    expected = _custom_settings(domain)

    repository.save(expected)
    result = repository.load()
    payload = json.loads((tmp_path / "config/codexbar/settings.json").read_text())

    assert result.settings == expected
    assert result.source_schema_version == 3
    assert payload == {
        "schema_version": 3,
        "low_remaining_threshold": "0.15",
        "refresh_interval_seconds": 120,
        "notifications_enabled": False,
        "usage_reserves": {},
        "usage_plan_checkpoints": {},
        "plan_breach_notifications_enabled": False,
    }


def test_snap_scoped_xdg_config_falls_back_to_host_home(tmp_path: Path) -> None:
    domain, infrastructure = _modules()
    home = tmp_path / "home"
    env = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "snap/code/999/.config"),
    }
    repository = infrastructure.JsonSettingsRepository(env=env)

    repository.save(_custom_settings(domain))

    assert (home / ".config/codexbar/settings.json").exists()
    assert not (home / "snap/code/999/.config/codexbar/settings.json").exists()


@pytest.mark.parametrize(
    "payload",
    [
        "{not-json",
        '{"schema_version": 1, "low_remaining_threshold": "2", '
        '"refresh_interval_seconds": 60, "notifications_enabled": true}',
        '{"schema_version": 99, "low_remaining_threshold": "0.2", '
        '"refresh_interval_seconds": 60, "notifications_enabled": true}',
        '{"schema_version": 1, "low_remaining_threshold": "0.2", '
        '"refresh_interval_seconds": 60, "notifications_enabled": true, "mystery": 1}',
    ],
)
def test_invalid_persisted_document_falls_back_with_diagnostic_without_overwrite(
    tmp_path: Path, payload: str
) -> None:
    domain, infrastructure = _modules()
    config = tmp_path / "config/codexbar"
    config.mkdir(parents=True)
    path = config / "settings.json"
    path.write_text(payload)
    env = {"HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)

    result = repository.load()

    assert result.settings == domain.AppSettings.defaults()
    assert result.diagnostic is not None
    assert path.read_text() == payload


def test_failed_replace_preserves_previous_valid_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    domain, infrastructure = _modules()
    env = {"HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)
    original = domain.AppSettings.defaults()
    repository.save(original)
    managed = tmp_path / "config/codexbar/settings.json"
    before = managed.read_bytes()

    def fail_replace(*_args, **_kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(infrastructure.os, "replace", fail_replace)

    with pytest.raises(SettingsWriteError, match="cannot write settings"):
        repository.save(_custom_settings(domain))

    assert managed.read_bytes() == before


def test_reset_is_idempotent_and_preserves_unrelated_files(tmp_path: Path) -> None:
    domain, infrastructure = _modules()
    env = {"HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)
    repository.save(_custom_settings(domain))
    unrelated = tmp_path / "config/codexbar/notes.txt"
    unrelated.write_text("keep")

    repository.reset()
    repository.reset()

    assert repository.load().settings == domain.AppSettings.defaults()
    assert unrelated.read_text() == "keep"
