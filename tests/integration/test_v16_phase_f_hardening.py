from __future__ import annotations

import importlib.util
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType

from codexbar.application.context import HistoricalContextReason
from codexbar.application.history import HistoryState
from codexbar.domain.context import ContextCoverage


def _load_phase_f_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "validate_phase_f_v16.py"
    )
    spec = importlib.util.spec_from_file_location(
        "codexbar_validate_phase_f_v16",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Phase F validator: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


phase_f = _load_phase_f_module()


def test_task_664_corruption_and_context_read_failure_are_isolated(
    tmp_path: Path,
) -> None:
    diagnostic = phase_f.fault_diagnostic(tmp_path)

    assert diagnostic.corrupt_history_state == HistoryState.UNREADABLE.value
    assert diagnostic.context_failure_reason == HistoricalContextReason.HISTORY_UNAVAILABLE.value


def test_task_665_unusual_sampling_gaps_preserve_tolerance_rule() -> None:
    diagnostic = phase_f.sampling_gap_diagnostic()

    assert diagnostic.historical_cycles == 4
    assert diagnostic.comparable_cycles == 2


def test_task_666_timezone_equivalent_instants_normalize_identically() -> None:
    assert phase_f.timezone_equivalent_instant_diagnostic()


def test_task_667_high_frequency_polling_does_not_create_pseudoreplication() -> None:
    diagnostic = phase_f.pseudoreplication_diagnostic()

    assert diagnostic.raw_observations == 63
    assert diagnostic.independent_cycles == 3


def test_task_669_tolerance_diagnostics_preserve_exact_rule_and_cap() -> None:
    diagnostics = phase_f.tolerance_diagnostics()
    values = {
        item.time_to_reset_hours: item.tolerance_seconds
        for item in diagnostics
    }

    assert values[Decimal("1")] == Decimal("180")
    assert values[Decimal("5")] == Decimal("900")
    assert values[Decimal("8")] == Decimal("1440")
    assert values[Decimal("24")] == Decimal("4320")
    assert values[Decimal("168")] == Decimal(str(timedelta(hours=2).total_seconds()))


def test_task_669_coverage_diagnostics_preserve_frozen_thresholds() -> None:
    diagnostics = {
        item.cycle_count: item.coverage
        for item in phase_f.coverage_diagnostics()
    }

    assert diagnostics[0] == ContextCoverage.INSUFFICIENT.value
    assert diagnostics[2] == ContextCoverage.INSUFFICIENT.value
    assert diagnostics[3] == ContextCoverage.SPARSE.value
    assert diagnostics[4] == ContextCoverage.SPARSE.value
    assert diagnostics[5] == ContextCoverage.LIMITED.value
    assert diagnostics[9] == ContextCoverage.LIMITED.value
    assert diagnostics[10] == ContextCoverage.ESTABLISHED.value
