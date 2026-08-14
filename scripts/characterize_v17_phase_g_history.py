#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from threading import Barrier

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryInterval,
)
from codexbar.application.history_policy import HISTORY_RETENTION
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

WINDOW_ID = UsageWindowId("phase-g-window")


@dataclass(frozen=True, slots=True)
class TimingSummary:
    count: int
    errors: int
    p50_ms: float
    p95_ms: float
    maximum_ms: float


@dataclass(frozen=True, slots=True)
class OperationSample:
    duration_ms: float
    error: str | None = None


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summary(samples: list[OperationSample]) -> TimingSummary:
    durations = [sample.duration_ms for sample in samples]
    return TimingSummary(
        count=len(samples),
        errors=sum(sample.error is not None for sample in samples),
        p50_ms=_quantile(durations, 0.50),
        p95_ms=_quantile(durations, 0.95),
        maximum_ms=max(durations),
    )


def _timed(callable_: Callable[[], object]) -> OperationSample:
    started = time.monotonic()
    try:
        callable_()
    except Exception as exc:  # characterization boundary records failures as evidence
        elapsed = (time.monotonic() - started) * 1000.0
        return OperationSample(elapsed, f"{type(exc).__name__}: {exc}")
    elapsed = (time.monotonic() - started) * 1000.0
    return OperationSample(elapsed)


def _snapshot(observed_at: datetime, index: int) -> HistoricalSnapshot:
    remaining = Decimal(50 + (index % 40)) / Decimal(100)
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=WINDOW_ID,
                label="Phase G window",
                remaining=Fraction(remaining),
                resets_at=observed_at + timedelta(hours=5),
            ),
        ),
    )


def _seed(repository: SqliteHistoryRepository, now: datetime) -> None:
    for index in range(80):
        repository.append(_snapshot(now - timedelta(days=40, minutes=index), index))
    for index in range(12):
        repository.append(
            _snapshot(
                now - HISTORY_RETENTION - timedelta(days=2, minutes=index),
                1000 + index,
            )
        )


def _journal_mode(path: Path, requested: str) -> str:
    with sqlite3.connect(path) as connection:
        row = connection.execute(f"PRAGMA journal_mode={requested}").fetchone()
    return str(row[0]).lower() if row else "unknown"


def _maintenance_characterization(
    path: Path,
    *,
    now: datetime,
    samples: int,
) -> dict[str, object]:
    repository = SqliteHistoryRepository(path)
    _seed(repository, now)

    append_samples: list[OperationSample] = []
    prune_samples: list[OperationSample] = []
    prune_counts: list[int] = []

    for index in range(samples):
        observed_at = now - timedelta(minutes=samples - index)
        append_samples.append(_timed(lambda index=index, observed_at=observed_at: repository.append(
            _snapshot(observed_at, 2000 + index)
        )))

        started = time.monotonic()
        try:
            removed = repository.prune(now - HISTORY_RETENTION)
            error = None
        except Exception as exc:  # characterization boundary
            removed = -1
            error = f"{type(exc).__name__}: {exc}"
        elapsed = (time.monotonic() - started) * 1000.0
        prune_samples.append(OperationSample(elapsed, error))
        prune_counts.append(removed)

    successful = [count for count in prune_counts if count >= 0]
    zero_effect = sum(count == 0 for count in successful)

    return {
        "append": asdict(_summary(append_samples)),
        "prune": asdict(_summary(prune_samples)),
        "prune_counts": prune_counts,
        "zero_effect_prunes": zero_effect,
        "successful_prunes": len(successful),
        "zero_effect_frequency": (
            zero_effect / len(successful) if successful else None
        ),
    }


def _concurrent_round(
    repository: SqliteHistoryRepository,
    context_repository: SqliteContextHistoryRepository,
    *,
    interval: HistoryInterval,
    cutoff: datetime,
    observed_at: datetime,
    index: int,
) -> dict[str, OperationSample]:
    barrier = Barrier(3)

    def writer() -> object:
        barrier.wait()
        repository.append(_snapshot(observed_at, 4000 + index))
        return repository.prune(cutoff)

    def history_reader() -> object:
        barrier.wait()
        return repository.query(interval)

    def context_reader() -> object:
        barrier.wait()
        return context_repository.query_candidates(WINDOW_ID, interval)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            "writer": executor.submit(_timed, writer),
            "history_read": executor.submit(_timed, history_reader),
            "context_read": executor.submit(_timed, context_reader),
        }
        return {name: future.result() for name, future in futures.items()}


def _concurrency_characterization(
    path: Path,
    *,
    requested_mode: str,
    now: datetime,
    samples: int,
) -> dict[str, object]:
    repository = SqliteHistoryRepository(path)
    _seed(repository, now)
    repository.prune(now - HISTORY_RETENTION)
    actual_mode = _journal_mode(path, requested_mode)

    repository = SqliteHistoryRepository(path)
    context_repository = SqliteContextHistoryRepository(repository)
    interval = HistoryInterval(now - timedelta(days=90), now + timedelta(days=1))

    collected: dict[str, list[OperationSample]] = {
        "writer": [],
        "history_read": [],
        "context_read": [],
    }
    errors: list[str] = []

    for index in range(samples):
        round_result = _concurrent_round(
            repository,
            context_repository,
            interval=interval,
            cutoff=now - HISTORY_RETENTION,
            observed_at=now - timedelta(seconds=samples - index),
            index=index,
        )
        for name, sample in round_result.items():
            collected[name].append(sample)
            if sample.error is not None:
                errors.append(f"{name}: {sample.error}")

    return {
        "requested_journal_mode": requested_mode.lower(),
        "actual_journal_mode": actual_mode,
        "operations": {
            name: asdict(_summary(samples_))
            for name, samples_ in collected.items()
        },
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Characterize v1.7 History maintenance and SQLite concurrency."
    )
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase G characterization requires at least 20 samples")

    now = datetime.now(UTC)
    with tempfile.TemporaryDirectory(prefix="codexbar-v17-phase-g-") as temporary:
        base = Path(temporary)
        maintenance = _maintenance_characterization(
            base / "maintenance.sqlite3",
            now=now,
            samples=args.samples,
        )
        concurrency = {
            mode: _concurrency_characterization(
                base / f"concurrency-{mode.lower()}.sqlite3",
                requested_mode=mode,
                now=now,
                samples=args.samples,
            )
            for mode in ("DELETE", "WAL")
        }

    payload = {
        "recorded_at": now.isoformat(),
        "samples": args.samples,
        "history_maintenance": maintenance,
        "concurrency": concurrency,
        "decision_policy": {
            "prune": (
                "retain current cadence unless measured zero-effect cost is material "
                "enough to justify redefining the 180-day maintenance contract"
            ),
            "wal": (
                "retain current journal mode unless DELETE shows meaningful lock/"
                "contention impact that WAL materially improves"
            ),
        },
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    print(encoded)

    if args.json_out is not None:
        args.json_out.write_text(encoded + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
