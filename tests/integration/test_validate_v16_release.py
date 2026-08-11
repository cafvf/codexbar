from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_validator() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "validate_v1_6.py"
    spec = importlib.util.spec_from_file_location("codexbar_validate_v1_6", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def test_v16_validator_preflight_targets_release_artifacts() -> None:
    names = {check.name for check in validator._preflight()}

    assert "pyproject.toml" in names
    assert "scripts/validate_phase_f_v16.py" in names
    assert "src/codexbar/application/context.py" in names
    assert "docs/validation/PHASE-F-HARDENING.md" in names


def test_v16_physical_checklist_is_explicit_and_non_destructive() -> None:
    checks = validator._physical_checklist()

    assert len(checks) >= 8
    assert all(check.status == "MANUAL" for check in checks)
