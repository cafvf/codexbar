from __future__ import annotations

import re
from pathlib import Path


def test_phase_h_read_only_validator_avoids_destructive_cli_commands() -> None:
    source = Path("scripts/validate_v17_phase_h.py").read_text(encoding="utf-8")

    assert '"settings", "reset"' not in source
    assert '"history", "clear"' not in source
    assert '"doctor", "--json"' in source
    assert '"history", "inspect"' in source
    assert '"reset-ledger", "inspect"' in source


def test_phase_h_read_only_validator_uses_canonical_codexbar_paths() -> None:
    source = Path("scripts/validate_v17_phase_h.py").read_text(encoding="utf-8")

    assert "history_database_path" in source
    assert "JsonSettingsRepository" in source
    assert "XDG_DATA_HOME" not in source
    assert "persistent_targets" in source


def test_phase_h_characterizer_carries_frozen_performance_budgets() -> None:
    source = Path("scripts/characterize_v17_phase_h.py").read_text(encoding="utf-8")

    for budget in ("500.0", "5.0", "50.0", "250.0", "150.0"):
        assert budget in source
    assert "PHASE_A_BASELINE_P95_MS" in source


def test_phase_h_characterizer_reads_phase_d_top_level_metric_shape() -> None:
    source = Path("scripts/characterize_v17_phase_h.py").read_text(encoding="utf-8")

    assert '_top_level_p95(phase_d, "context.qt_sync")' in source
    assert "_characterize_local_doctor" in source
    assert "--phase-a-attempts" in source


def test_phase_h_release_evidence_preserves_single_authority_decision() -> None:
    runtime = Path("src/codexbar/__init__.py").read_text(encoding="utf-8")
    evidence = Path(
        "docs/specs/v1.7/evidence/PHASE-H-VALIDATION-RELEASE.md"
    ).read_text(encoding="utf-8")

    assert 'distribution_version("codexbar")' in runtime
    assert re.search(r'__version__\s*=\s*"\d+\.\d+\.\d+"', runtime) is None
    assert "H2 — release preparation" in evidence
    assert "`pyproject.toml` is `1.7.0`;" in evidence
    assert "`uv.lock` contains CodexBar `1.7.0`;" in evidence
