#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from codexbar.application.redeem import RedeemAttempt, RedeemProcessStatus, RedeemResult
from codexbar.application.redeem_execution import (
    RedeemExecutionController,
    RedeemExecutionPhase,
)
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.reset import ResetCreditId


@dataclass(frozen=True, slots=True)
class TimingSummary:
    sample_count: int
    p50_ms: float
    p95_ms: float
    minimum_ms: float
    maximum_ms: float


class DelayedRedeemManager:
    def __init__(self, delay_seconds: float) -> None:
        self._delay = delay_seconds
        self._counter = 0

    def redeem(self, *, credit_id: ResetCreditId | None = None) -> RedeemResult:
        self._counter += 1
        time.sleep(self._delay)
        return RedeemResult(
            RedeemAttempt(
                RedeemAttemptId(f"characterize-{self._counter}"),
                credit_id,
                RedeemProcessStatus.SUCCEEDED,
            )
        )

    def retry(self, attempt_id: RedeemAttemptId) -> RedeemResult:
        time.sleep(self._delay)
        return RedeemResult(
            RedeemAttempt(attempt_id, None, RedeemProcessStatus.ALREADY_REDEEMED)
        )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Characterize Phase E submission responsiveness with a delayed fake."
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--delay-ms", type=float, default=200.0)
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase E characterization requires at least 20 samples")
    if args.delay_ms <= 0:
        raise SystemExit("delay must be positive")

    manager = DelayedRedeemManager(args.delay_ms / 1000.0)
    controller = RedeemExecutionController(manager)
    submissions: list[float] = []
    totals: list[float] = []
    try:
        for index in range(args.samples):
            started = time.monotonic()
            before_submit = time.monotonic()
            accepted = controller.start_redeem(
                credit_id=ResetCreditId(f"fake-{index}")
            )
            submissions.append((time.monotonic() - before_submit) * 1000.0)
            if not accepted:
                raise SystemExit("redeem controller rejected delayed-fake start")

            deadline = time.monotonic() + 3.0
            state = controller.state
            while time.monotonic() < deadline:
                state = controller.poll()
                if not controller.busy:
                    break
                time.sleep(0.001)
            else:
                raise SystemExit("delayed-fake redeem timed out")
            if state.phase is not RedeemExecutionPhase.RESULT:
                raise SystemExit(f"delayed fake ended in {state.phase.value}")
            totals.append((time.monotonic() - started) * 1000.0)

        submit_summary = _summary(submissions)
        total_summary = _summary(totals)
        responsive = submit_summary.p95_ms <= 50.0
        separated = total_summary.p50_ms >= args.delay_ms * 0.8
        passed = responsive and separated
        generated_at = datetime.now(UTC).isoformat()

        print("CodexBar v1.7 Phase E delayed-fake redeem characterization")
        print(f"Generated: {generated_at}")
        print(f"Injected external delay: {args.delay_ms:.1f} ms")
        print(
            "redeem.ui_submit: "
            f"n={submit_summary.sample_count} p50={submit_summary.p50_ms:.3f} ms "
            f"p95={submit_summary.p95_ms:.3f} ms min={submit_summary.minimum_ms:.3f} ms "
            f"max={submit_summary.maximum_ms:.3f} ms"
        )
        print(
            "redeem.background_total: "
            f"n={total_summary.sample_count} p50={total_summary.p50_ms:.3f} ms "
            f"p95={total_summary.p95_ms:.3f} ms min={total_summary.minimum_ms:.3f} ms "
            f"max={total_summary.maximum_ms:.3f} ms"
        )
        print(f"Responsiveness separation: {'PASS' if passed else 'FAIL'}")

        if args.json_out is not None:
            payload = {
                "generated_at": generated_at,
                "samples": args.samples,
                "delay_ms": args.delay_ms,
                "redeem.ui_submit": asdict(submit_summary),
                "redeem.background_total": asdict(total_summary),
                "responsiveness_pass": passed,
            }
            args.json_out.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"Evidence JSON: {args.json_out}")
        return 0 if passed else 1
    finally:
        controller.close()


if __name__ == "__main__":
    raise SystemExit(main())
