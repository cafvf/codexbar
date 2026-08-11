#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path

from codexbar import __version__
from codexbar.application.context import HistoricalContextService
from codexbar.application.history import HistoryInterval, HistoryState
from codexbar.infrastructure.account_rate_limits import parse_account_rate_limits_response
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.app_server import CodexAppServerGateway, SubprocessJsonRpcTransport
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.diagnostics import build_doctor_service
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository


@dataclass(frozen=True, slots=True)
class TimingSummary:
    sample_count: int
    p50_ms: float
    p95_ms: float
    minimum_ms: float
    maximum_ms: float


@dataclass(frozen=True, slots=True)
class PhaseACharacterization:
    generated_at: str
    codexbar_version: str
    python_version: str
    platform: str
    samples: int
    timings: dict[str, TimingSummary]
    notes: tuple[str, ...]


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires samples")
    index = (len(ordered) - 1) * probability
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = index - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * fraction


def _summary(values: Sequence[float]) -> TimingSummary:
    if not values:
        raise ValueError("timing summary requires samples")
    return TimingSummary(
        sample_count=len(values),
        p50_ms=_quantile(values, 0.50),
        p95_ms=_quantile(values, 0.95),
        minimum_ms=min(values),
        maximum_ms=max(values),
    )


def _time_call[T](call: Callable[[], T]) -> tuple[T, float]:
    started = time.monotonic()
    result = call()
    elapsed_ms = (time.monotonic() - started) * 1000.0
    return result, elapsed_ms


def _characterize_app_server(samples: int) -> tuple[dict[str, TimingSummary], object]:
    raw: dict[str, list[float]] = {
        "app_server.spawn": [],
        "app_server.initialize": [],
        "app_server.request": [],
        "app_server.parse": [],
        "app_server.shutdown": [],
        "app_server.total": [],
    }
    last_observation: object = None
    gateway = CodexAppServerGateway()

    for _ in range(samples):
        total_started = time.monotonic()
        transport, spawn_ms = _time_call(SubprocessJsonRpcTransport)
        raw["app_server.spawn"].append(spawn_ms)
        try:
            _, initialize_ms = _time_call(partial(gateway._initialize, transport))
            raw["app_server.initialize"].append(initialize_ms)
            response, request_ms = _time_call(
                partial(
                    gateway._request,
                    transport,
                    request_id=1,
                    method="account/rateLimits/read",
                    params=None,
                )
            )
            raw["app_server.request"].append(request_ms)
            observed_at = datetime.now(UTC)
            last_observation, parse_ms = _time_call(
                partial(
                    parse_account_rate_limits_response,
                    response,
                    observed_at=observed_at,
                )
            )
            raw["app_server.parse"].append(parse_ms)
        finally:
            _, shutdown_ms = _time_call(transport.close)
            raw["app_server.shutdown"].append(shutdown_ms)
        raw["app_server.total"].append((time.monotonic() - total_started) * 1000.0)

    return {key: _summary(values) for key, values in raw.items()}, last_observation


def _characterize_current(samples: int) -> tuple[TimingSummary, object]:
    reader = CodexAccountRateLimitsReader()
    durations: list[float] = []
    last = None
    for _ in range(samples):
        last, elapsed = _time_call(reader.read_account_rate_limits)
        durations.append(elapsed)
    return _summary(durations), last


def _characterize_local_doctor(samples: int) -> TimingSummary:
    durations: list[float] = []
    for _ in range(samples):
        service = build_doctor_service(include_source_probe=False)
        _, elapsed = _time_call(service.collect)
        durations.append(elapsed)
    return _summary(durations)


def _characterize_history_and_context(
    samples: int,
    current_observation: object,
) -> tuple[dict[str, TimingSummary], tuple[str, ...]]:
    notes: list[str] = []
    timings: dict[str, TimingSummary] = {}
    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    if inspection.state not in {HistoryState.READY_EMPTY, HistoryState.READY_NON_EMPTY}:
        notes.append(f"History characterization unavailable: state={inspection.state.value}")
        return timings, tuple(notes)
    if not hasattr(current_observation, "usage"):
        notes.append("Context characterization unavailable: no Current observation")
        return timings, tuple(notes)

    repository = SqliteHistoryRepository(path)
    usage = current_observation.usage
    end = usage.observed_at

    for days in (30, 180):
        interval = HistoryInterval(end - timedelta(days=days), end)
        durations: list[float] = []
        for _ in range(samples):
            _, elapsed = _time_call(lambda interval=interval: repository.query(interval))
            durations.append(elapsed)
        timings[f"history.read_{days}d"] = _summary(durations)

    if not usage.windows:
        notes.append("Context characterization unavailable: Current has no usage windows")
        return timings, tuple(notes)

    window_id = usage.windows[0].id
    context_repository = SqliteContextHistoryRepository(repository)
    interval_180 = HistoryInterval(end - timedelta(days=180), end)
    candidate_durations: list[float] = []
    for _ in range(samples):
        _, elapsed = _time_call(
            lambda: context_repository.query_candidates(window_id, interval_180)
        )
        candidate_durations.append(elapsed)
    timings["context.candidate_read"] = _summary(candidate_durations)

    cold: list[float] = []
    for _ in range(samples):
        context_service = HistoricalContextService(context_repository)
        _, elapsed = _time_call(
            lambda service=context_service: service.evaluate(
                current=usage,
                window_id=window_id,
            )
        )
        cold.append(elapsed)
    timings["context.cold"] = _summary(cold)

    context_service = HistoricalContextService(context_repository)
    repeated: list[float] = []
    for _ in range(samples):
        _, elapsed = _time_call(
            lambda: context_service.evaluate(current=usage, window_id=window_id)
        )
        repeated.append(elapsed)
    timings["context.repeated_v16_behavior"] = _summary(repeated)
    return timings, tuple(notes)


def characterize(samples: int) -> PhaseACharacterization:
    if samples < 20:
        raise ValueError("Phase A characterization needs at least 20 samples for p95 evidence")

    timings, _ = _characterize_app_server(samples)
    current_summary, current_observation = _characterize_current(samples)
    timings["current.full_read"] = current_summary
    timings["doctor.local_only"] = _characterize_local_doctor(samples)
    history_timings, notes = _characterize_history_and_context(samples, current_observation)
    timings.update(history_timings)

    return PhaseACharacterization(
        generated_at=datetime.now(UTC).isoformat(),
        codexbar_version=__version__,
        python_version=platform.python_version(),
        platform=f"{platform.system()} {platform.release()}",
        samples=samples,
        timings=timings,
        notes=notes,
    )


def _print_report(report: PhaseACharacterization) -> None:
    print("CodexBar v1.7 Phase A characterization")
    print(f"Generated: {report.generated_at}")
    print(f"CodexBar: {report.codexbar_version}")
    print(f"Python: {report.python_version}")
    print(f"Platform: {report.platform}")
    print(f"Samples: {report.samples}")
    print()
    for key, value in sorted(report.timings.items()):
        print(
            f"{key}: n={value.sample_count} "
            f"p50={value.p50_ms:.3f} ms p95={value.p95_ms:.3f} ms "
            f"min={value.minimum_ms:.3f} ms max={value.maximum_ms:.3f} ms"
        )
    for note in report.notes:
        print(f"NOTE: {note}")


def _json_payload(report: PhaseACharacterization) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "codexbar_version": report.codexbar_version,
        "python_version": report.python_version,
        "platform": report.platform,
        "samples": report.samples,
        "timings": {key: asdict(value) for key, value in report.timings.items()},
        "notes": list(report.notes),
    }


def _write_json(path: Path, report: PhaseACharacterization) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_json_payload(report), indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Characterize CodexBar v1.7 Phase A hot paths.")
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = characterize(args.samples)
    _print_report(report)
    if args.json_out is not None:
        _write_json(args.json_out, report)
        print(f"Evidence JSON: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
