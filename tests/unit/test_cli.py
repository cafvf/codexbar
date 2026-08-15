from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from codexbar.__main__ import main
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import UsagePlanCheckpoint, UsagePlanCheckpointPolicy
from codexbar.infrastructure.settings import JsonSettingsRepository


def test_cli_mock_smoke(capsys) -> None:
    assert main(["--mock"]) == 0
    output = capsys.readouterr().out
    assert "CodexBar" in output
    assert "Weekly: 81% left" in output


def test_settings_show_reports_defaults_and_origin(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    assert main(["settings", "show"]) == 0

    output = capsys.readouterr().out
    assert "Origin: defaults" in output
    assert "LOW remaining threshold: 20%" in output
    assert "Refresh interval: 60 seconds" in output
    assert "Notifications: enabled" in output
    assert "Plan breach notifications: disabled" in output
    assert "Settings schema source: defaults" in output
    assert "Usage Plan checkpoints: none" in output


def test_settings_show_reports_persisted_origin(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config/codexbar/settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        """{
  "schema_version": 1,
  "low_remaining_threshold": "0.12",
  "refresh_interval_seconds": 180,
  "notifications_enabled": false
}
""",
        encoding="utf-8",
    )

    assert main(["settings", "show"]) == 0

    output = capsys.readouterr().out
    assert "Origin: persisted" in output
    assert "LOW remaining threshold: 12%" in output
    assert "Refresh interval: 180 seconds" in output
    assert "Notifications: disabled" in output
    assert "Plan breach notifications: disabled" in output
    assert "Settings schema source: 1" in output
    assert "Usage Plan checkpoints: none" in output


def test_settings_show_reports_plan_configuration_deterministically(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    repository = JsonSettingsRepository()
    weekly = UsageWindowId("opaque-weekly")
    settings = repository.load().settings.with_usage_plan_checkpoints(
        UsagePlanCheckpointPolicy(
            (
                UsagePlanCheckpoint(
                    weekly,
                    TimeToReset(timedelta(hours=24)),
                    Fraction(Decimal("0.30")),
                ),
                UsagePlanCheckpoint(
                    weekly,
                    TimeToReset(timedelta(hours=72)),
                    Fraction(Decimal("0.55")),
                ),
            )
        )
    ).with_plan_breach_notifications_enabled(True)
    repository.save(settings)

    assert main(["settings", "show"]) == 0

    output = capsys.readouterr().out
    assert "Origin: persisted" in output
    assert "Settings schema source: 3" in output
    assert "Plan breach notifications: enabled" in output
    assert "Usage Plan checkpoints:" in output
    assert "opaque-weekly: 259200 seconds -> minimum 55%" in output
    assert "opaque-weekly: 86400 seconds -> minimum 30%" in output
    assert output.index("259200 seconds") < output.index("86400 seconds")


def test_settings_show_surfaces_diagnostic_without_crashing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config/codexbar/settings.json"
    path.parent.mkdir(parents=True)
    path.write_text("{broken", encoding="utf-8")

    assert main(["settings", "show"]) == 0

    captured = capsys.readouterr()
    assert "Origin: defaults" in captured.out
    assert "Diagnostic:" in captured.out
    assert path.read_text(encoding="utf-8") == "{broken"


def test_settings_reset_uses_application_behavior_and_preserves_neighbors(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    repository = JsonSettingsRepository()
    path = repository.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """{
  "schema_version": 1,
  "low_remaining_threshold": "0.12",
  "refresh_interval_seconds": 180,
  "notifications_enabled": false
}
""",
        encoding="utf-8",
    )
    neighbor = path.parent / "keep.txt"
    neighbor.write_text("keep", encoding="utf-8")

    assert main(["settings", "reset"]) == 0

    output = capsys.readouterr().out
    assert "Settings reset to defaults." in output
    assert not path.exists()
    assert neighbor.read_text(encoding="utf-8") == "keep"
