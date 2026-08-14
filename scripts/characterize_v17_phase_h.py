#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from codexbar.infrastructure.diagnostics import build_doctor_service

DOCTOR_LOCAL_BUDGET_P95_MS = 500.0
CONTEXT_CACHE_HIT_BUDGET_P95_MS = 5.0
CONTEXT_QT_SYNC_BUDGET_P95_MS = 50.0
IPC_SHOW_DETAILS_BUDGET_P95_MS = 250.0
CONTEXT_COLD_TARGET_P95_MS = 150.0

PHASE_A_BASELINE_P95_MS = {
    "app_server.spawn": 1.613,
    "app_server.initialize": 329.143,
    "app_server.request": 912.809,
    "app_server.parse": 0.235,
    "app_server.shutdown": 31.784,
    "app_server.total": 1235.441,
    "current.full_read": 1222.721,
    "doctor.local_only": 1.634,
    "history.read_30d": 38.492,
    "history.read_180d": 38.202,
    "context.candidate_read": 14.502,
    "context.cold": 21.328,
    "context.repeated_v16_behavior": 27.211,
}


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _run_json_script(
    script: str,
    output: Path,
    *,
    samples: int,
    extra: tuple[str, ...] = (),
) -> tuple[int, str, str, dict[str, object] | None]:
    argv = [
        sys.executable,
        script,
        "--samples",
        str(samples),
        "--json-out",
        str(output),
        *extra,
    ]
    completed = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        check=False,
    )
    payload: dict[str, object] | None = None
    if output.exists():
        decoded = json.loads(output.read_text(encoding="utf-8"))
        if isinstance(decoded, dict):
            payload = decoded
    return completed.returncode, completed.stdout, completed.stderr, payload


def _run_phase_a_with_retries(
    base: Path,
    *,
    samples: int,
    attempts: int,
) -> tuple[
    tuple[int, str, str, dict[str, object] | None],
    list[dict[str, object]],
]:
    diagnostics: list[dict[str, object]] = []
    last: tuple[int, str, str, dict[str, object] | None] = (1, "", "", None)

    for attempt in range(1, attempts + 1):
        output = base / f"phase-a-final-attempt-{attempt}.json"
        last = _run_json_script(
            "scripts/characterize_v17_phase_a.py",
            output,
            samples=samples,
        )
        diagnostics.append(
            {
                "attempt": attempt,
                "exit": last[0],
                "stderr": last[2],
                "payload_available": last[3] is not None,
            }
        )
        if last[0] == 0 and last[3] is not None:
            break

    return last, diagnostics


def _timing_p95(
    payload: dict[str, object] | None,
    timing_name: str,
) -> float | None:
    if payload is None:
        return None
    timings = _mapping(payload.get("timings"))
    timing = _mapping(timings.get(timing_name))
    raw = timing.get("p95_ms")
    if isinstance(raw, int | float):
        return float(raw)
    return None


def _top_level_p95(
    payload: dict[str, object] | None,
    field_name: str,
) -> float | None:
    if payload is None:
        return None
    summary = _mapping(payload.get(field_name))
    raw = summary.get("p95_ms")
    if isinstance(raw, int | float):
        return float(raw)
    return None


def _bool_field(payload: dict[str, object] | None, name: str) -> bool:
    return bool(payload is not None and payload.get(name) is True)


def _characterize_local_doctor(samples: int) -> dict[str, object]:
    durations: list[float] = []
    for _ in range(samples):
        service = build_doctor_service(include_source_probe=False)
        started = time.monotonic()
        service.collect()
        durations.append((time.monotonic() - started) * 1000.0)

    return {
        "sample_count": len(durations),
        "p50_ms": _quantile(durations, 0.50),
        "p95_ms": _quantile(durations, 0.95),
        "minimum_ms": min(durations),
        "maximum_ms": max(durations),
    }


def _doctor_p95(summary: dict[str, object]) -> float | None:
    raw = summary.get("p95_ms")
    if isinstance(raw, int | float):
        return float(raw)
    return None


def _final_metric_p95(
    name: str,
    *,
    phase_a: dict[str, object] | None,
    phase_c: dict[str, object] | None,
    doctor_local: dict[str, object],
) -> tuple[float | None, str]:
    if name == "doctor.local_only":
        return _doctor_p95(doctor_local), "phase_h_local_doctor"
    if name in {"context.candidate_read", "context.cold"}:
        return _timing_p95(phase_c, name), "phase_c_final"
    return _timing_p95(phase_a, name), "phase_a_final"


def _phase_a_comparison(
    phase_a: dict[str, object] | None,
    phase_c: dict[str, object] | None,
    doctor_local: dict[str, object],
) -> dict[str, object]:
    comparison: dict[str, object] = {}
    for name, baseline in PHASE_A_BASELINE_P95_MS.items():
        final, source = _final_metric_p95(
            name,
            phase_a=phase_a,
            phase_c=phase_c,
            doctor_local=doctor_local,
        )
        if final is None:
            comparison[name] = {
                "available": False,
                "baseline_p95_ms": baseline,
                "source": source,
            }
            continue
        comparison[name] = {
            "available": True,
            "baseline_p95_ms": baseline,
            "final_p95_ms": final,
            "delta_ms": final - baseline,
            "ratio": final / baseline if baseline else None,
            "source": source,
        }
    return comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run final CodexBar v1.7 target performance characterization."
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--phase-a-attempts", type=int, default=3)
    parser.add_argument("--with-ipc", action="store_true")
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 20:
        raise SystemExit("Phase H characterization requires at least 20 samples")
    if args.phase_a_attempts < 1:
        raise SystemExit("--phase-a-attempts must be at least 1")

    with tempfile.TemporaryDirectory(prefix="codexbar-v17-h-") as temporary:
        base = Path(temporary)
        phase_a_run, phase_a_attempts = _run_phase_a_with_retries(
            base,
            samples=args.samples,
            attempts=args.phase_a_attempts,
        )
        phase_c_run = _run_json_script(
            "scripts/characterize_v17_phase_c.py",
            base / "phase-c-final.json",
            samples=args.samples,
        )
        phase_d_run = _run_json_script(
            "scripts/characterize_v17_phase_d.py",
            base / "phase-d-final.json",
            samples=args.samples,
        )

        ipc_run: tuple[int, str, str, dict[str, object] | None] | None = None
        if args.with_ipc:
            ipc_run = _run_json_script(
                "scripts/characterize_v17_phase_b.py",
                base / "phase-b-final.json",
                samples=args.samples,
            )

        phase_a = phase_a_run[3]
        phase_c = phase_c_run[3]
        phase_d = phase_d_run[3]
        phase_b = ipc_run[3] if ipc_run is not None else None
        doctor_local = _characterize_local_doctor(args.samples)

        doctor_p95 = _doctor_p95(doctor_local)
        cache_hit_p95 = _timing_p95(phase_c, "context.cache_hit")
        qt_sync_p95 = _top_level_p95(phase_d, "context.qt_sync")

        hard_checks = {
            "phase_a_completed": phase_a_run[0] == 0 and phase_a is not None,
            "phase_c_completed": phase_c_run[0] == 0 and phase_c is not None,
            "phase_d_completed": phase_d_run[0] == 0 and phase_d is not None,
            "doctor_local_p95_le_500ms": bool(
                doctor_p95 is not None
                and doctor_p95 <= DOCTOR_LOCAL_BUDGET_P95_MS
            ),
            "context_cache_hit_p95_le_5ms": bool(
                _bool_field(phase_c, "cache_hit_budget_pass")
                and cache_hit_p95 is not None
                and cache_hit_p95 <= CONTEXT_CACHE_HIT_BUDGET_P95_MS
            ),
            "context_qt_sync_p95_le_50ms": bool(
                _bool_field(phase_d, "qt_sync_budget_pass")
                and qt_sync_p95 is not None
                and qt_sync_p95 <= CONTEXT_QT_SYNC_BUDGET_P95_MS
            ),
        }

        if args.with_ipc:
            ipc_p95 = None
            if phase_b is not None:
                show_details = _mapping(phase_b.get("show_details"))
                raw_ipc = show_details.get("p95_ms")
                if isinstance(raw_ipc, int | float):
                    ipc_p95 = float(raw_ipc)
            hard_checks["ipc_p95_le_250ms"] = bool(
                ipc_run
                and ipc_run[0] == 0
                and _bool_field(phase_b, "budget_pass")
                and ipc_p95 is not None
                and ipc_p95 <= IPC_SHOW_DETAILS_BUDGET_P95_MS
            )

        cold_p95 = _timing_p95(phase_c, "context.cold")
        cold_target_pass = (
            cold_p95 <= CONTEXT_COLD_TARGET_P95_MS
            if cold_p95 is not None
            else None
        )

        payload = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "samples": args.samples,
            "budgets_ms": {
                "doctor_local_p95": DOCTOR_LOCAL_BUDGET_P95_MS,
                "context_cache_hit_p95": CONTEXT_CACHE_HIT_BUDGET_P95_MS,
                "context_qt_sync_p95": CONTEXT_QT_SYNC_BUDGET_P95_MS,
                "show_details_ipc_p95": IPC_SHOW_DETAILS_BUDGET_P95_MS,
                "context_cold_engineering_target_p95": CONTEXT_COLD_TARGET_P95_MS,
            },
            "hard_checks": hard_checks,
            "cold_context_engineering_target": {
                "p95_ms": cold_p95,
                "target_p95_ms": CONTEXT_COLD_TARGET_P95_MS,
                "pass": cold_target_pass,
                "release_blocking_alone": False,
            },
            "doctor_local_final": doctor_local,
            "phase_a_final": phase_a,
            "phase_c_final": phase_c,
            "phase_d_final": phase_d,
            "phase_b_ipc_final": (
                phase_b
                if args.with_ipc
                else {
                    "status": "SKIP",
                    "reason": (
                        "rerun with --with-ipc while one GUI owner is running"
                    ),
                }
            ),
            "phase_a_p95_comparison": _phase_a_comparison(
                phase_a,
                phase_c,
                doctor_local,
            ),
            "command_diagnostics": {
                "phase_a": {
                    "attempts": phase_a_attempts,
                    "final_exit": phase_a_run[0],
                    "final_stderr": phase_a_run[2],
                },
                "phase_c": {
                    "exit": phase_c_run[0],
                    "stderr": phase_c_run[2],
                },
                "phase_d": {
                    "exit": phase_d_run[0],
                    "stderr": phase_d_run[2],
                },
                "phase_b": (
                    {"exit": ipc_run[0], "stderr": ipc_run[2]}
                    if ipc_run is not None
                    else {"status": "SKIP"}
                ),
            },
            "overall_hard_pass": all(hard_checks.values()),
        }

    encoded = json.dumps(payload, indent=2, sort_keys=True)
    print(encoded)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded + "\n", encoding="utf-8")

    return 0 if payload["overall_hard_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
