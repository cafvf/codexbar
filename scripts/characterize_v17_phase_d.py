#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from codexbar.composition import build_gui_runtime
from codexbar.ui.context_controller import ContextControllerPhase


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


def _timed[T](callable_: Callable[[], T]) -> tuple[T, float]:
    started = time.monotonic()
    result = callable_()
    return result, (time.monotonic() - started) * 1000.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Characterize v1.7 Phase D asynchronous Context orchestration."
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--mock", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase D characterization requires at least 20 samples")

    runtime = build_gui_runtime(mock=args.mock)
    try:
        runtime.provider.get_usage()
        controller = runtime.context_controller
        synchronous: list[float] = []
        background: list[float] = []

        for _ in range(args.samples):
            runtime.context_service.clear_cache()
            started = time.monotonic()
            accepted, elapsed = _timed(controller.start)
            synchronous.append(elapsed)
            if not accepted:
                raise SystemExit("Context controller rejected characterization start")

            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                _, poll_elapsed = _timed(controller.poll)
                synchronous.append(poll_elapsed)
                if not controller.busy:
                    break
                time.sleep(0.001)
            else:
                raise SystemExit("Context background characterization timed out")

            if controller.state.phase is not ContextControllerPhase.READY:
                raise SystemExit(
                    f"Context did not become ready: {controller.state.phase.value}"
                )
            background.append((time.monotonic() - started) * 1000.0)

        sync_summary = _summary(synchronous)
        background_summary = _summary(background)
        budget_pass = sync_summary.p95_ms <= 50.0
        generated_at = datetime.now(UTC).isoformat()

        print("CodexBar v1.7 Phase D async Context characterization")
        print(f"Generated: {generated_at}")
        print(
            "context.qt_sync: "
            f"n={sync_summary.sample_count} p50={sync_summary.p50_ms:.3f} ms "
            f"p95={sync_summary.p95_ms:.3f} ms min={sync_summary.minimum_ms:.3f} ms "
            f"max={sync_summary.maximum_ms:.3f} ms"
        )
        print(
            "context.background_cold: "
            f"n={background_summary.sample_count} p50={background_summary.p50_ms:.3f} ms "
            f"p95={background_summary.p95_ms:.3f} ms "
            f"min={background_summary.minimum_ms:.3f} ms "
            f"max={background_summary.maximum_ms:.3f} ms"
        )
        print(
            "Qt Context blocking budget: "
            f"{'PASS' if budget_pass else 'FAIL'} (p95 <= 50 ms)"
        )

        if args.json_out is not None:
            payload = {
                "generated_at": generated_at,
                "samples": args.samples,
                "mock": args.mock,
                "context.qt_sync": asdict(sync_summary),
                "context.background_cold": asdict(background_summary),
                "qt_sync_budget_p95_ms": 50.0,
                "qt_sync_budget_pass": budget_pass,
            }
            args.json_out.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"Evidence JSON: {args.json_out}")
        return 0 if budget_pass else 1
    finally:
        runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
