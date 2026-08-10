#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_DAYS = 180
DEFAULT_POLL_MINUTES = 15
DEFAULT_REPEATS = 15
FIXTURE_END = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)

SCHEMA_SQL = """
CREATE TABLE history_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY,
    observed_at_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    rate_limit_reached_type TEXT,
    observation_key TEXT NOT NULL UNIQUE
);
CREATE TABLE window_observations (
    snapshot_id INTEGER NOT NULL,
    window_id TEXT NOT NULL,
    label TEXT NOT NULL,
    remaining TEXT NOT NULL,
    resets_at_utc TEXT,
    PRIMARY KEY (snapshot_id, window_id),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);
CREATE INDEX idx_snapshots_observed_at ON snapshots(observed_at_utc, id);
CREATE INDEX idx_windows_window_id_snapshot
    ON window_observations(window_id, snapshot_id);
"""


@dataclass(frozen=True, slots=True)
class FixtureSummary:
    days: int
    poll_minutes: int
    snapshots: int
    window_rows: int
    snapshots_per_day: float
    window_rows_per_day: float
    database_bytes: int
    bytes_per_day: float
    projected_180_day_bytes: int


@dataclass(frozen=True, slots=True)
class TimingSummary:
    repeats: int
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float


@dataclass(frozen=True, slots=True)
class CharacterizationReport:
    schema_version: int
    fixture: FixtureSummary
    history_30d_query: TimingSummary
    window_180d_query: TimingSummary
    context_candidate_query: TimingSummary
    query_plans: dict[str, list[str]]
    index_decision: str


def format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def deterministic_rows(
    *,
    days: int,
    poll_minutes: int,
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    if days <= 0:
        raise ValueError("days must be positive")
    if poll_minutes <= 0:
        raise ValueError("poll_minutes must be positive")

    start = FIXTURE_END - timedelta(days=days)
    step = timedelta(minutes=poll_minutes)
    snapshot_rows: list[tuple[Any, ...]] = []
    window_rows: list[tuple[Any, ...]] = []
    observed_at = start
    snapshot_id = 1

    while observed_at < FIXTURE_END:
        observed = format_timestamp(observed_at)
        snapshot_rows.append(
            (snapshot_id, observed, "mock", None, f"fixture-{snapshot_id:08d}")
        )

        primary_cycle_hours = 8
        secondary_cycle_days = 7
        primary_reset = _next_boundary(observed_at, timedelta(hours=primary_cycle_hours))
        secondary_reset = _next_boundary(observed_at, timedelta(days=secondary_cycle_days))
        primary_remaining = _remaining_fraction(
            observed_at, primary_reset, primary_cycle_hours * 3600
        )
        secondary_remaining = _remaining_fraction(
            observed_at,
            secondary_reset,
            secondary_cycle_days * 86400,
        )

        window_rows.extend(
            (
                (
                    snapshot_id,
                    "context_primary",
                    "Primary context window",
                    primary_remaining,
                    format_timestamp(primary_reset),
                ),
                (
                    snapshot_id,
                    "context_secondary",
                    "Secondary context window",
                    secondary_remaining,
                    format_timestamp(secondary_reset),
                ),
            )
        )
        snapshot_id += 1
        observed_at += step

    return snapshot_rows, window_rows


def _next_boundary(value: datetime, duration: timedelta) -> datetime:
    seconds = int(duration.total_seconds())
    epoch = int(value.timestamp())
    next_epoch = ((epoch // seconds) + 1) * seconds
    return datetime.fromtimestamp(next_epoch, tz=UTC)


def _remaining_fraction(observed_at: datetime, reset_at: datetime, cycle_seconds: int) -> str:
    fraction = (reset_at - observed_at).total_seconds() / cycle_seconds
    bounded = min(1.0, max(0.0, fraction))
    return f"{bounded:.6f}"


def create_fixture(path: Path, *, days: int, poll_minutes: int) -> FixtureSummary:
    snapshot_rows, window_rows = deterministic_rows(days=days, poll_minutes=poll_minutes)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT INTO history_meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        connection.executemany(
            """
            INSERT INTO snapshots(
                id, observed_at_utc, source, rate_limit_reached_type, observation_key
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            snapshot_rows,
        )
        connection.executemany(
            """
            INSERT INTO window_observations(
                snapshot_id, window_id, label, remaining, resets_at_utc
            ) VALUES (?, ?, ?, ?, ?)
            """,
            window_rows,
        )
        connection.execute("ANALYZE")

    database_bytes = path.stat().st_size
    snapshots = len(snapshot_rows)
    windows = len(window_rows)
    return FixtureSummary(
        days=days,
        poll_minutes=poll_minutes,
        snapshots=snapshots,
        window_rows=windows,
        snapshots_per_day=snapshots / days,
        window_rows_per_day=windows / days,
        database_bytes=database_bytes,
        bytes_per_day=database_bytes / days,
        projected_180_day_bytes=math.ceil(database_bytes / days * 180),
    )


def percentile_linear(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate percentile of empty values")
    index = (len(ordered) - 1) * p
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def benchmark(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...],
    repeats: int,
) -> TimingSummary:
    connection.execute(sql, params).fetchall()
    timings: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        connection.execute(sql, params).fetchall()
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        timings.append(elapsed_ms)
    return TimingSummary(
        repeats=repeats,
        median_ms=statistics.median(timings),
        p95_ms=percentile_linear(timings, 0.95),
        min_ms=min(timings),
        max_ms=max(timings),
    )


def explain(connection: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[str]:
    rows = connection.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return [str(row[3]) for row in rows]


def characterize(path: Path, *, fixture: FixtureSummary, repeats: int) -> CharacterizationReport:
    end = format_timestamp(FIXTURE_END)
    start_30d = format_timestamp(FIXTURE_END - timedelta(days=30))
    start_180d = format_timestamp(FIXTURE_END - timedelta(days=fixture.days))

    window_sql = """
        SELECT s.observed_at_utc, s.source, w.label, w.remaining, w.resets_at_utc
        FROM window_observations AS w
        JOIN snapshots AS s ON s.id = w.snapshot_id
        WHERE w.window_id = ? AND s.observed_at_utc >= ? AND s.observed_at_utc < ?
        ORDER BY s.observed_at_utc ASC, s.id ASC
    """
    candidate_sql = """
        SELECT s.observed_at_utc, w.remaining, w.resets_at_utc
        FROM window_observations AS w
        JOIN snapshots AS s ON s.id = w.snapshot_id
        WHERE
            w.window_id = ?
            AND w.resets_at_utc IS NOT NULL
            AND s.observed_at_utc >= ?
            AND s.observed_at_utc < ?
        ORDER BY w.resets_at_utc ASC, s.observed_at_utc ASC
    """

    with sqlite3.connect(path) as connection:
        history_params = ("context_primary", start_30d, end)
        window_params = ("context_primary", start_180d, end)
        candidate_params = ("context_primary", start_180d, end)
        history = benchmark(connection, window_sql, history_params, repeats)
        window = benchmark(connection, window_sql, window_params, repeats)
        candidate = benchmark(connection, candidate_sql, candidate_params, repeats)
        plans = {
            "history_30d": explain(connection, window_sql, history_params),
            "window_180d": explain(connection, window_sql, window_params),
            "context_candidate": explain(connection, candidate_sql, candidate_params),
        }

    decision = (
        "Retain schema v1 and existing indexes for Phase A. The candidate Context query is "
        "characterized but no speculative index is added; index changes remain evidence-driven."
    )
    return CharacterizationReport(
        schema_version=SCHEMA_VERSION,
        fixture=fixture,
        history_30d_query=history,
        window_180d_query=window,
        context_candidate_query=candidate,
        query_plans=plans,
        index_decision=decision,
    )


def markdown_report(report: CharacterizationReport) -> str:
    fixture = report.fixture
    timing_rows = [
        ("History window 30d", report.history_30d_query),
        ("Window 180d", report.window_180d_query),
        ("Context candidate 180d", report.context_candidate_query),
    ]
    timing_table = "\n".join(
        f"| {label} | {timing.median_ms:.3f} | {timing.p95_ms:.3f} | "
        f"{timing.min_ms:.3f} | {timing.max_ms:.3f} |"
        for label, timing in timing_rows
    )
    return f"""# CodexBar v1.6 Phase A — History Characterization

Schema: v{report.schema_version}
Fixture: {fixture.days} days, {fixture.poll_minutes}-minute polling, two dynamic test windows.

## Storage

- snapshots: {fixture.snapshots}
- window rows: {fixture.window_rows}
- snapshots/day: {fixture.snapshots_per_day:.2f}
- database bytes: {fixture.database_bytes}
- bytes/day: {fixture.bytes_per_day:.2f}
- projected 180-day bytes: {fixture.projected_180_day_bytes}

## Query timings

| Query | Median (ms) | p95 (ms) | Min (ms) | Max (ms) |
|---|---:|---:|---:|---:|
{timing_table}

## Query plans

```json
{json.dumps(report.query_plans, indent=2)}
```

## Phase A persistence decision

{report.index_decision}

These figures are characterization evidence, not hard CI performance thresholds. Re-run the
script on the target workstation when validating the phase to collect machine-local evidence.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Characterize schema-v1 history at 180-day retention"
    )
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--poll-minutes", type=int, default=DEFAULT_POLL_MINUTES)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="codexbar-v16-history-") as temporary:
        path = Path(temporary) / "history.sqlite3"
        fixture = create_fixture(path, days=args.days, poll_minutes=args.poll_minutes)
        report = characterize(path, fixture=fixture, repeats=args.repeats)
        rendered = json.dumps(asdict(report), indent=2) if args.as_json else markdown_report(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
