#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from codexbar.application.context import HistoricalContextService
from codexbar.application.history import HistoryInterval, HistoryState
from codexbar.application.history_policy import HISTORY_RETENTION
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository


@dataclass(frozen=True, slots=True)
class TimingSummary:
    sample_count: int
    p50_ms: float
    p95_ms: float
    minimum_ms: float
    maximum_ms: float


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summary(values: list[float]) -> TimingSummary:
    return TimingSummary(
        sample_count=len(values),
        p50_ms=_quantile(values, 0.50),
        p95_ms=_quantile(values, 0.95),
        minimum_ms=min(values),
        maximum_ms=max(values),
    )


def _time_call[T](callable_: Callable[[], T]) -> tuple[T, float]:
    started = time.monotonic()
    result = callable_()
    return result, (time.monotonic() - started) * 1000.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Characterize v1.7 Phase C lean Context query and revision cache."
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase C characterization requires at least 20 samples")

    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    if inspection.state not in {HistoryState.READY_EMPTY, HistoryState.READY_NON_EMPTY}:
        raise SystemExit(f"History is not readable for characterization: {inspection.state.value}")

    current = CodexAccountRateLimitsReader().read_account_rate_limits().usage
    window = next((item for item in current.windows if item.resets_at is not None), None)
    if window is None:
        raise SystemExit("Current has no window with a reset timestamp to characterize")

    repository = SqliteHistoryRepository(path)
    context_repository = SqliteContextHistoryRepository(repository)
    service = HistoricalContextService(context_repository)
    current_revision = CurrentRevision(1)
    history_revision = HistoryRevision(1)
    interval = HistoryInterval(current.observed_at - HISTORY_RETENTION, current.observed_at)

    candidate_durations: list[float] = []
    cold_durations: list[float] = []
    cache_hit_durations: list[float] = []
    semantic_equal = True

    for _ in range(args.samples):
        _, elapsed = _time_call(
            lambda: context_repository.query_candidates(window.id, interval)
        )
        candidate_durations.append(elapsed)

    for _ in range(args.samples):
        service.clear_cache()
        cold, elapsed = _time_call(
            lambda: service.evaluate(
                current=current,
                window_id=window.id,
                current_revision=current_revision,
                history_revision=history_revision,
            )
        )
        cold_durations.append(elapsed)
        cached, hit_elapsed = _time_call(
            lambda: service.evaluate(
                current=current,
                window_id=window.id,
                current_revision=current_revision,
                history_revision=history_revision,
            )
        )
        cache_hit_durations.append(hit_elapsed)
        semantic_equal = semantic_equal and cached == cold

    summaries = {
        "context.candidate_read": _summary(candidate_durations),
        "context.cold": _summary(cold_durations),
        "context.cache_hit": _summary(cache_hit_durations),
    }
    generated_at = datetime.now(UTC).isoformat()
    cache_budget_pass = summaries["context.cache_hit"].p95_ms <= 5.0

    print("CodexBar v1.7 Phase C Context runtime characterization")
    print(f"Generated: {generated_at}")
    print(f"History: {path}")
    print(f"History snapshots: {inspection.snapshot_count}")
    print(f"Window: {window.id.value}")
    for name, summary in summaries.items():
        print(
            f"{name}: n={summary.sample_count} p50={summary.p50_ms:.3f} ms "
            f"p95={summary.p95_ms:.3f} ms min={summary.minimum_ms:.3f} ms "
            f"max={summary.maximum_ms:.3f} ms"
        )
    print(f"Semantic equivalence: {'PASS' if semantic_equal else 'FAIL'}")
    print(
        "Cache-hit budget: "
        f"{'PASS' if cache_budget_pass else 'FAIL'} (p95 <= 5 ms)"
    )

    if args.json_out is not None:
        payload = {
            "generated_at": generated_at,
            "history_path": str(path),
            "history_snapshot_count": inspection.snapshot_count,
            "window_id": window.id.value,
            "samples": args.samples,
            "timings": {name: asdict(summary) for name, summary in summaries.items()},
            "semantic_equivalence": semantic_equal,
            "cache_hit_budget_p95_ms": 5.0,
            "cache_hit_budget_pass": cache_budget_pass,
        }
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Evidence JSON: {args.json_out}")

    return 0 if semantic_equal and cache_budget_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
