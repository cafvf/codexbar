#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType

from codexbar.application.context import (
    FailedContextHistoryRepository,
    HistoricalContextReason,
    HistoricalContextService,
)
from codexbar.application.history import HistoryReadError, HistoryState
from codexbar.domain.context import (
    ContextCoverage,
    ContextObservation,
    TimeToReset,
    contextual_tolerance,
    select_context_references,
)
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

FIXTURE_END = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)
WINDOW_ID = UsageWindowId("context_primary")
DEFAULT_REPEATS = 25


def _load_characterization() -> ModuleType:
    path = Path(__file__).with_name("characterize_history_v16.py")
    spec = importlib.util.spec_from_file_location(
        "codexbar_characterize_history_v16_phase_f",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load characterization script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_characterization()


@dataclass(frozen=True, slots=True)
class ToleranceDiagnostic:
    time_to_reset_hours: Decimal
    tolerance_seconds: Decimal


@dataclass(frozen=True, slots=True)
class CoverageDiagnostic:
    cycle_count: int
    coverage: str


@dataclass(frozen=True, slots=True)
class FaultDiagnostic:
    corrupt_history_state: str
    context_failure_reason: str


@dataclass(frozen=True, slots=True)
class GapDiagnostic:
    historical_cycles: int
    comparable_cycles: int


@dataclass(frozen=True, slots=True)
class PseudoreplicationDiagnostic:
    raw_observations: int
    independent_cycles: int


@dataclass(frozen=True, slots=True)
class PhaseFReport:
    characterization: dict[str, object]
    tolerance: tuple[ToleranceDiagnostic, ...]
    coverage: tuple[CoverageDiagnostic, ...]
    faults: FaultDiagnostic
    sampling_gap: GapDiagnostic
    timezone_equivalent_instants: bool
    pseudoreplication: PseudoreplicationDiagnostic
    schema_decision: str


def _fraction(value: str) -> Fraction:
    return Fraction(Decimal(value))


def _current_snapshot() -> UsageSnapshot:
    reset = FIXTURE_END + timedelta(hours=4)
    return UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW_ID,
                "Primary context window",
                _fraction("0.50"),
                resets_at=reset,
            ),
        ),
        observed_at=FIXTURE_END,
        source=UsageSource.MOCK,
    )


def tolerance_diagnostics() -> tuple[ToleranceDiagnostic, ...]:
    hours = (Decimal("1"), Decimal("5"), Decimal("8"), Decimal("24"), Decimal("168"))
    diagnostics = []
    for value in hours:
        duration = timedelta(seconds=float(value * Decimal(3600)))
        tolerance = contextual_tolerance(TimeToReset(duration))
        diagnostics.append(
            ToleranceDiagnostic(
                time_to_reset_hours=value,
                tolerance_seconds=Decimal(str(tolerance.total_seconds())),
            )
        )
    return tuple(diagnostics)


def coverage_diagnostics() -> tuple[CoverageDiagnostic, ...]:
    counts = (0, 1, 2, 3, 4, 5, 9, 10, 20)
    return tuple(
        CoverageDiagnostic(
            cycle_count=count,
            coverage=ContextCoverage.from_cycle_count(count).value,
        )
        for count in counts
    )


def fault_diagnostic(directory: Path) -> FaultDiagnostic:
    corrupt = directory / "corrupt-history.sqlite3"
    corrupt.write_bytes(b"not-a-sqlite-database")
    inspection = SqliteHistoryRepository.inspect_path(corrupt)

    service = HistoricalContextService(
        FailedContextHistoryRepository(HistoryReadError("injected history failure"))
    )
    result = service.evaluate(current=_current_snapshot(), window_id=WINDOW_ID)

    return FaultDiagnostic(
        corrupt_history_state=inspection.state.value,
        context_failure_reason=(
            result.reason.value if result.reason is not None else "missing"
        ),
    )


def sampling_gap_diagnostic() -> GapDiagnostic:
    current = ContextObservation(
        window_id=WINDOW_ID,
        observed_at=FIXTURE_END,
        remaining=_fraction("0.50"),
        resets_at=FIXTURE_END + timedelta(hours=4),
    )
    history = (
        _historical_cycle(days_ago=7, mismatch_minutes=5, remaining="0.40"),
        _historical_cycle(days_ago=14, mismatch_minutes=11, remaining="0.45"),
        _historical_cycle(days_ago=21, mismatch_minutes=13, remaining="0.55"),
        _historical_cycle(days_ago=28, mismatch_minutes=30, remaining="0.60"),
    )
    selection = select_context_references(current=current, historical=history)
    reference_set = selection.reference_set
    comparable = reference_set.cycle_count if reference_set is not None else 0
    return GapDiagnostic(
        historical_cycles=len(history),
        comparable_cycles=comparable,
    )


def _historical_cycle(
    *,
    days_ago: int,
    mismatch_minutes: int,
    remaining: str,
) -> ContextObservation:
    reset = FIXTURE_END - timedelta(days=days_ago) + timedelta(hours=4)
    observed = reset - timedelta(hours=4, minutes=mismatch_minutes)
    return ContextObservation(
        window_id=WINDOW_ID,
        observed_at=observed,
        remaining=_fraction(remaining),
        resets_at=reset,
    )


def timezone_equivalent_instant_diagnostic() -> bool:
    utc_observed = datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    utc_reset = datetime(2026, 11, 1, 9, 30, tzinfo=UTC)
    offset = timezone(timedelta(hours=-4))
    local_observed = utc_observed.astimezone(offset)
    local_reset = utc_reset.astimezone(offset)
    return TimeToReset.from_instants(
        observed_at=utc_observed,
        resets_at=utc_reset,
    ) == TimeToReset.from_instants(
        observed_at=local_observed,
        resets_at=local_reset,
    )


def pseudoreplication_diagnostic() -> PseudoreplicationDiagnostic:
    current = ContextObservation(
        window_id=WINDOW_ID,
        observed_at=FIXTURE_END,
        remaining=_fraction("0.50"),
        resets_at=FIXTURE_END + timedelta(hours=4),
    )
    observations = []
    for cycle_index in range(1, 4):
        reset = FIXTURE_END - timedelta(days=cycle_index * 7) + timedelta(hours=4)
        for minute_offset in range(-10, 11):
            observed = reset - timedelta(hours=4, minutes=minute_offset)
            observations.append(
                ContextObservation(
                    window_id=WINDOW_ID,
                    observed_at=observed,
                    remaining=_fraction(f"0.{cycle_index + 3}0"),
                    resets_at=reset,
                )
            )
    selection = select_context_references(
        current=current,
        historical=tuple(observations),
    )
    reference_set = selection.reference_set
    return PseudoreplicationDiagnostic(
        raw_observations=len(observations),
        independent_cycles=reference_set.cycle_count if reference_set else 0,
    )


def build_report(
    *,
    days: int,
    poll_minutes: int,
    repeats: int,
) -> PhaseFReport:
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    with tempfile.TemporaryDirectory(prefix="codexbar-v16-phase-f-") as temporary:
        directory = Path(temporary)
        database = directory / "history.sqlite3"
        fixture = base.create_fixture(
            database,
            days=days,
            poll_minutes=poll_minutes,
        )
        characterization = base.characterize(
            database,
            fixture=fixture,
            repeats=repeats,
        )
        faults = fault_diagnostic(directory)

    return PhaseFReport(
        characterization=asdict(characterization),
        tolerance=tolerance_diagnostics(),
        coverage=coverage_diagnostics(),
        faults=faults,
        sampling_gap=sampling_gap_diagnostic(),
        timezone_equivalent_instants=timezone_equivalent_instant_diagnostic(),
        pseudoreplication=pseudoreplication_diagnostic(),
        schema_decision=(
            "Retain schema v1. No Phase F schema/index migration is introduced; "
            "performance remains evidence-driven."
        ),
    )


def validate_report(report: PhaseFReport) -> tuple[str, ...]:
    failures = []
    fixture = report.characterization["fixture"]
    if not isinstance(fixture, dict) or fixture.get("days") != 180:
        failures.append("TASK-660 requires a 180-day characterization")
    if report.faults.corrupt_history_state != HistoryState.UNREADABLE.value:
        failures.append("TASK-664 corrupt history must be classified unreadable")
    if (
        report.faults.context_failure_reason
        != HistoricalContextReason.HISTORY_UNAVAILABLE.value
    ):
        failures.append("TASK-664 Context history failure must remain isolated")
    if report.sampling_gap.comparable_cycles != 2:
        failures.append("TASK-665 sampling-gap fixture selected unexpected cycles")
    if not report.timezone_equivalent_instants:
        failures.append("TASK-666 equivalent instants changed time-to-reset")
    if report.pseudoreplication.independent_cycles != 3:
        failures.append("TASK-667 polling frequency changed independent-cycle count")
    if report.pseudoreplication.raw_observations <= report.pseudoreplication.independent_cycles:
        failures.append("TASK-667 fixture does not exercise repeated polling")
    return tuple(failures)


def markdown_report(report: PhaseFReport) -> str:
    characterization = report.characterization
    fixture = characterization["fixture"]
    history = characterization["history_30d_query"]
    window = characterization["window_180d_query"]
    candidate = characterization["context_candidate_query"]
    context = characterization["production_context_summary"]

    tolerance_rows = "\n".join(
        f"| {item.time_to_reset_hours} | {item.tolerance_seconds} |"
        for item in report.tolerance
    )
    coverage_rows = "\n".join(
        f"| {item.cycle_count} | {item.coverage} |"
        for item in report.coverage
    )
    failures = validate_report(report)
    gate = "PASS" if not failures else "FAIL"

    return f"""# CodexBar v1.6 — Phase F Performance + Hardening

Gate F: **{gate}**

## TASK-660..663 — 180-day scale and performance

- schema: v{characterization["schema_version"]}
- days: {fixture["days"]}
- polling: {fixture["poll_minutes"]} minutes
- snapshots: {fixture["snapshots"]}
- window rows: {fixture["window_rows"]}
- database bytes: {fixture["database_bytes"]}
- projected 180-day bytes: {fixture["projected_180_day_bytes"]}
- History 30d p50/p95: {history["median_ms"]:.3f}/{history["p95_ms"]:.3f} ms
- Window 180d p50/p95: {window["median_ms"]:.3f}/{window["p95_ms"]:.3f} ms
- Context candidate SQL p50/p95: {candidate["median_ms"]:.3f}/{candidate["p95_ms"]:.3f} ms
- Production Context p50/p95: {context["median_ms"]:.3f}/{context["p95_ms"]:.3f} ms
- decision: {report.schema_decision}

## TASK-664..667 — hardening regressions

- corrupt history state: {report.faults.corrupt_history_state}
- Context read failure: {report.faults.context_failure_reason}
- sampling-gap comparable cycles: {report.sampling_gap.comparable_cycles}
- timezone/DST-equivalent instants: {report.timezone_equivalent_instants}
- high-frequency raw observations: {report.pseudoreplication.raw_observations}
- independent historical cycles: {report.pseudoreplication.independent_cycles}

## TASK-669 — tolerance diagnostics

| h* (hours) | tolerance (seconds) |
|---:|---:|
{tolerance_rows}

## TASK-669 — coverage diagnostics

| independent cycles | coverage |
|---:|---|
{coverage_rows}

## Gate diagnostics

{json.dumps(list(failures), indent=2)}

Performance numbers are machine-local characterization evidence, not CI thresholds.
The full v1.5 protected-baseline gate remains the normal pytest/ruff/mypy/compileall gate.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run CodexBar v1.6 Phase F performance and hardening evidence"
    )
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--poll-minutes", type=int, default=15)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        days=args.days,
        poll_minutes=args.poll_minutes,
        repeats=args.repeats,
    )
    failures = validate_report(report)
    rendered = (
        json.dumps(asdict(report), indent=2)
        if args.as_json
        else markdown_report(report)
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
