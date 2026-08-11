from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_phase_f_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "validate_phase_f_v16.py"
    )
    spec = importlib.util.spec_from_file_location(
        "codexbar_validate_phase_f_v16_unit",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Phase F validator: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


phase_f = _load_phase_f_module()


def test_task_660_663_small_characterization_keeps_schema_v1(tmp_path: Path) -> None:
    report = phase_f.build_report(days=3, poll_minutes=30, repeats=2)
    characterization = report.characterization
    fixture = characterization["fixture"]

    assert characterization["schema_version"] == 1
    assert fixture["days"] == 3
    assert fixture["snapshots"] == 144
    assert fixture["window_rows"] == 288
    assert characterization["history_30d_query"]["repeats"] == 2
    assert characterization["window_180d_query"]["repeats"] == 2
    assert characterization["production_context_summary"]["repeats"] == 2
    assert report.schema_decision.startswith("Retain schema v1")


def test_phase_f_report_validation_requires_real_180_day_evidence() -> None:
    report = phase_f.build_report(days=2, poll_minutes=60, repeats=1)

    failures = phase_f.validate_report(report)

    assert "TASK-660 requires a 180-day characterization" in failures
