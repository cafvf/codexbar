from __future__ import annotations

from pathlib import Path


def test_ci_covers_all_declared_python_minors() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    for minor in ("3.12", "3.13", "3.14"):
        assert f'- "{minor}"' in workflow


def test_ci_runs_the_frozen_headless_quality_gate() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    required = (
        "pytest -ra",
        "ruff check src tests scripts",
        "mypy",
        "python -m compileall -q src scripts",
        "pytest -q tests/architecture",
    )
    assert all(command in workflow for command in required)


def test_ci_keeps_physical_native_validation_out_of_hosted_gate() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8").lower()

    assert "--diagnose-indicator" not in workflow
    assert "characterize_v17_phase_g_history.py" not in workflow
    assert "qt_qpa_platform: offscreen" in workflow
