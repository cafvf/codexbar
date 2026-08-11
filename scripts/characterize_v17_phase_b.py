#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from codexbar.application.instance_ownership import InstanceCommand, InstanceReply
from codexbar.ui.instance_ownership import instance_endpoint_name, send_instance_command


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Characterize v1.7 Phase B SHOW_DETAILS IPC against a running GUI owner."
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase B characterization requires at least 20 samples")

    endpoint = instance_endpoint_name()
    durations: list[float] = []
    for index in range(args.samples):
        started = time.monotonic()
        reply = send_instance_command(
            endpoint,
            InstanceCommand.SHOW_DETAILS,
            timeout_ms=250,
        )
        elapsed_ms = (time.monotonic() - started) * 1000.0
        if reply is not InstanceReply.OK:
            raise SystemExit(
                f"sample {index + 1}: no live owner accepted SHOW_DETAILS "
                f"(reply={reply!r}); start `uv run codexbar --gui` first"
            )
        durations.append(elapsed_ms)

    summary = _summary(durations)
    generated_at = datetime.now(UTC).isoformat()
    print("CodexBar v1.7 Phase B IPC characterization")
    print(f"Generated: {generated_at}")
    print(f"Endpoint: {endpoint}")
    print(
        "SHOW_DETAILS: "
        f"n={summary.sample_count} p50={summary.p50_ms:.3f} ms "
        f"p95={summary.p95_ms:.3f} ms min={summary.minimum_ms:.3f} ms "
        f"max={summary.maximum_ms:.3f} ms"
    )
    print(f"Budget: {'PASS' if summary.p95_ms <= 250.0 else 'FAIL'} (p95 <= 250 ms)")

    if args.json_out is not None:
        payload = {
            "generated_at": generated_at,
            "endpoint": endpoint,
            "show_details": asdict(summary),
            "budget_p95_ms": 250.0,
            "budget_pass": summary.p95_ms <= 250.0,
        }
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Evidence JSON: {args.json_out}")
    return 0 if summary.p95_ms <= 250.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
