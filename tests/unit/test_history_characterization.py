from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_characterization_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "characterize_history_v16.py"
    )
    spec = importlib.util.spec_from_file_location(
        "codexbar_characterize_history_v16",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load characterization script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


characterization = _load_characterization_module()
DEFAULT_DAYS = characterization.DEFAULT_DAYS
DEFAULT_POLL_MINUTES = characterization.DEFAULT_POLL_MINUTES
characterize = characterization.characterize
create_fixture = characterization.create_fixture
deterministic_rows = characterization.deterministic_rows
percentile_linear = characterization.percentile_linear


def test_task_614_fixture_generator_is_deterministic() -> None:
    first = deterministic_rows(days=2, poll_minutes=30)
    second = deterministic_rows(days=2, poll_minutes=30)

    assert first == second
    assert len(first[0]) == 96
    assert len(first[1]) == 192


def test_task_614_default_fixture_has_expected_180_day_row_counts() -> None:
    snapshots, windows = deterministic_rows(
        days=DEFAULT_DAYS,
        poll_minutes=DEFAULT_POLL_MINUTES,
    )

    assert len(snapshots) == 17_280
    assert len(windows) == 34_560


def test_task_615_617_characterization_preserves_schema_v1(tmp_path: Path) -> None:
    path = tmp_path / "history.sqlite3"
    fixture = create_fixture(path, days=3, poll_minutes=30)
    report = characterize(path, fixture=fixture, repeats=2)

    with sqlite3.connect(path) as connection:
        schema_version = connection.execute(
            "SELECT value FROM history_meta WHERE key = 'schema_version'"
        ).fetchone()[0]

    assert schema_version == "1"
    assert report.schema_version == 1
    assert fixture.snapshots == 144
    assert fixture.window_rows == 288
    assert report.history_30d_query.repeats == 2
    assert report.window_180d_query.repeats == 2
    assert report.context_candidate_query.repeats == 2
    assert report.production_context_summary.repeats == 2
    assert "Retain schema v1" in report.index_decision


def test_characterization_percentile_uses_explicit_linear_interpolation() -> None:
    assert percentile_linear([0.0, 10.0, 20.0, 30.0], 0.95) == pytest.approx(28.5)
