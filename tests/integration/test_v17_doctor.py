from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import codexbar.__main__ as main_module
from codexbar.application.diagnostics import (
    DiagnosticProvider,
    DiagnosticService,
    render_doctor_json,
    render_doctor_text,
)
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    DiagnosticFreshness,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)
from codexbar.domain.errors import UsageSourceUnavailableError
from codexbar.infrastructure.diagnostics import build_doctor_service

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class SensitiveFakeProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.fake"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        return (
            SubsystemHealth(
                name="fake",
                role=SubsystemRole.ENVIRONMENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                summary=(
                    "account person@example.com Bearer abc.def.ghi "
                    "access_token=super-secret-value "
                    "sk-abcdefghijklmnopqrstuvwxyz "
                    '{"refresh_token":"refresh-super-secret"}'
                ),
                details=(
                    DiagnosticDetail("email", "person@example.com"),
                    DiagnosticDetail("access_token", "super-secret-value"),
                    DiagnosticDetail("safe", "visible person@example.com"),
                ),
            ),
        )


class StaticDoctorService:
    def __init__(self, snapshot: SystemHealthSnapshot) -> None:
        self._snapshot = snapshot

    def collect(self) -> SystemHealthSnapshot:
        return self._snapshot


def _healthy_snapshot() -> SystemHealthSnapshot:
    return SystemHealthSnapshot(
        generated_at=NOW,
        subsystems=(
            SubsystemHealth(
                name="environment",
                role=SubsystemRole.ENVIRONMENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.LOCAL_PERSISTED_INSPECTION,
                summary="healthy",
            ),
        ),
    )


def test_doctor_local_only_does_not_create_settings_history_or_ledger(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    config_home = tmp_path / "config"
    data_home = tmp_path / "data"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    snapshot = build_doctor_service(include_source_probe=False).collect()

    assert snapshot.generated_at.tzinfo is not None
    assert not (config_home / "codexbar" / "settings.json").exists()
    assert not (data_home / "codexbar" / "history.sqlite3").exists()
    assert not (data_home / "codexbar" / "reset-ledger.sqlite3").exists()


def test_local_runtime_and_qt_discovery_are_fresh_read_only_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    snapshot = build_doctor_service(include_source_probe=False).collect()
    by_name = {item.name: item for item in snapshot.subsystems}

    assert (
        by_name["runtime_environment"].evidence_origin
        is EvidenceOrigin.FRESH_READ_ONLY_PROBE
    )
    assert by_name["qt_fallback"].evidence_origin is EvidenceOrigin.FRESH_READ_ONLY_PROBE


def test_doctor_json_schema_v1_and_lineage_limitation_are_explicit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    document = json.loads(
        render_doctor_json(build_doctor_service(include_source_probe=False).collect())
    )

    assert document["diagnostics_schema_version"] == 1
    lineage = next(item for item in document["subsystems"] if item["name"] == "history_lineage")
    assert lineage["details"]["mode"] == "single_account_assumption"
    assert lineage["details"]["account_namespaced"] is False


def test_tv_1712_text_and_json_minimize_email_token_and_auth_material() -> None:
    service = DiagnosticService(
        providers=(SensitiveFakeProvider(),),
        runtime_metrics=RuntimeMetricCollector(),
        clock=lambda: NOW,
    )
    snapshot = service.collect()

    text = render_doctor_text(snapshot)
    encoded = render_doctor_json(snapshot)

    for output in (text, encoded):
        assert "person@example.com" not in output
        assert "super-secret-value" not in output
        assert "abcdefghijklmnopqrstuvwxyz" not in output
        assert "refresh-super-secret" not in output
    document = json.loads(encoded)
    details = document["subsystems"][0]["details"]
    assert "email" not in details
    assert "access_token" not in details
    assert details["safe"] == "visible <redacted-email>"


def test_doctor_cli_text_and_json_use_same_snapshot_model(monkeypatch, capsys) -> None:
    snapshot = _healthy_snapshot()
    monkeypatch.setattr(
        main_module,
        "build_doctor_service",
        lambda: StaticDoctorService(snapshot),
    )

    assert main_module.main(["doctor"]) == 0
    text_output = capsys.readouterr().out
    assert "Overall: healthy" in text_output

    assert main_module.main(["doctor", "--json"]) == 0
    json_output = capsys.readouterr().out
    document = json.loads(json_output)
    assert document["diagnostics_schema_version"] == 1
    assert document["overall_health"] == "healthy"
    assert document["subsystems"][0]["name"] == "environment"


def _file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def test_doctor_local_inspection_does_not_modify_existing_persistent_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from codexbar.domain.settings import AppSettings
    from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository
    from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
    from codexbar.infrastructure.settings import JsonSettingsRepository

    home = tmp_path / "home"
    config_home = tmp_path / "config"
    data_home = tmp_path / "data"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    settings_repository = JsonSettingsRepository()
    settings_repository.save(AppSettings.defaults())
    history_path = data_home / "codexbar" / "history.sqlite3"
    reset_path = data_home / "codexbar" / "reset-ledger.sqlite3"
    SqliteHistoryRepository(history_path)
    SqliteResetEventRepository(reset_path)

    tracked = (settings_repository.path, history_path, reset_path)
    before = {path: _file_bytes(path) for path in tracked}
    directory_before = tuple(sorted(path.name for path in (data_home / "codexbar").iterdir()))

    build_doctor_service(include_source_probe=False).collect()

    assert {path: _file_bytes(path) for path in tracked} == before
    directory_after = tuple(
        sorted(path.name for path in (data_home / "codexbar").iterdir())
    )
    assert directory_after == directory_before


def test_malformed_history_is_reported_without_repair_or_traceback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    data_home = tmp_path / "data"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    history_path = data_home / "codexbar" / "history.sqlite3"
    history_path.parent.mkdir(parents=True)
    original = b"not-a-sqlite-database"
    history_path.write_bytes(original)

    snapshot = build_doctor_service(include_source_probe=False).collect()
    history = next(item for item in snapshot.subsystems if item.name == "history")

    assert history.availability is DiagnosticAvailability.UNAVAILABLE
    assert history.operational_health is OperationalHealth.FAILED
    assert history_path.read_bytes() == original


class FailingSourceReader:
    def read_account_rate_limits(self):
        raise UsageSourceUnavailableError("source unavailable")


def test_expected_source_failure_becomes_diagnostic_state() -> None:
    snapshot = build_doctor_service(source_reader=FailingSourceReader()).collect()
    source = next(item for item in snapshot.subsystems if item.name == "codex_source")
    current = next(item for item in snapshot.subsystems if item.name == "current")

    assert source.operational_health is OperationalHealth.FAILED
    assert current.availability is DiagnosticAvailability.UNAVAILABLE
    assert snapshot.overall_health.value == "needs_attention"


def test_doctor_text_reports_degraded_stale_current() -> None:
    snapshot = SystemHealthSnapshot(
        generated_at=NOW,
        subsystems=(
            SubsystemHealth(
                name="codex_source",
                role=SubsystemRole.SOURCE,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                summary="source healthy",
            ),
            SubsystemHealth(
                name="current",
                role=SubsystemRole.CURRENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                freshness=DiagnosticFreshness.STALE,
                summary="using last known Current",
            ),
        ),
    )

    assert "Overall: degraded" in render_doctor_text(snapshot)
