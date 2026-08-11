from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from codexbar.application.context import (
    HistoricalContextReason,
    HistoricalContextService,
    HistoricalContextState,
)
from codexbar.domain.models import UsageWindowId
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: str
    detail: str


def _print(check: Check) -> None:
    print(f"[{check.status}] {check.name}: {check.detail}")


def _run(command: list[str]) -> Check:
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    detail = completed.stdout.strip() or completed.stderr.strip() or f"exit={completed.returncode}"
    return Check(
        " ".join(command),
        "PASS" if completed.returncode == 0 else "FAIL",
        detail,
    )


def _preflight() -> list[Check]:
    required = [
        Path("pyproject.toml"),
        Path("scripts/validate_phase_f_v16.py"),
        Path("src/codexbar/application/context.py"),
        Path("src/codexbar/infrastructure/context_history.py"),
        Path("src/codexbar/ui/context_viewmodel.py"),
        Path("docs/validation/PHASE-F-HARDENING.md"),
    ]
    return [
        Check(
            str(path),
            "PASS" if path.exists() else "FAIL",
            "present" if path.exists() else "missing",
        )
        for path in required
    ]


def _version_check() -> Check:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    expected = 'version = "1.6.0"'
    return Check(
        "project version",
        "PASS" if expected in text else "FAIL",
        "1.6.0" if expected in text else "pyproject.toml is not 1.6.0",
    )


def _history_check() -> Check:
    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    status = "FAIL" if inspection.state.value in {"unreadable", "unsupported"} else "PASS"
    detail = (
        f"path={inspection.path}; state={inspection.state.value}; "
        f"schema={inspection.schema_version or 'n/a'}; snapshots={inspection.snapshot_count}"
    )
    return Check("real history inspect", status, detail)


def _real_context_check() -> Check:
    try:
        observation = CodexAccountRateLimitsReader().read_account_rate_limits()
    except Exception as exc:
        return Check(
            "real CURRENT Context",
            "SKIP",
            f"current account capability/source unavailable: {exc}",
        )

    current = observation.usage
    eligible = tuple(window for window in current.windows if window.resets_at is not None)
    if not eligible:
        return Check(
            "real CURRENT Context",
            "SKIP",
            "current source reported no window with authoritative resets_at",
        )

    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    if inspection.state.value in {"absent", "unreadable", "unsupported"}:
        return Check(
            "real CURRENT Context",
            "SKIP",
            f"history capability unavailable: state={inspection.state.value}",
        )

    repository = SqliteHistoryRepository(path)
    service = HistoricalContextService(SqliteContextHistoryRepository(repository))
    results = [
        service.evaluate(current=current, window_id=UsageWindowId(window.id.value))
        for window in eligible
    ]

    bad = [
        result
        for result in results
        if result.state is HistoricalContextState.UNAVAILABLE
        and result.reason
        in {
            HistoricalContextReason.CURRENT_NOT_CURRENT,
            HistoricalContextReason.CURRENT_RESET_INVALID,
            HistoricalContextReason.HISTORY_UNAVAILABLE,
        }
    ]
    if bad:
        details = ", ".join(
            f"{result.window_id.value}:{result.reason.value if result.reason else 'unknown'}"
            for result in bad
        )
        return Check("real CURRENT Context", "FAIL", details)

    detail = ", ".join(
        f"{result.window_id.value}:{result.state.value}"
        + (
            f":N={result.comparable_cycle_count}"
            if result.comparable_cycle_count is not None
            else ""
        )
        for result in results
    )
    return Check("real CURRENT Context", "PASS", detail)


def _absence_state_check() -> Check:
    check = _run(
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "tests/unit/test_context_application.py",
            "tests/unit/test_context_viewmodel.py",
            "tests/integration/test_v16_phase_f_hardening.py",
        ]
    )
    return Check("Context absence-state regression", check.status, check.detail)


def _side_effect_check() -> Check:
    check = _run(
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "tests/architecture/test_v16_phase_f_protected_baseline.py",
            "tests/architecture/test_v16_context_application_architecture.py",
            "tests/architecture/test_v16_context_ui_architecture.py",
        ]
    )
    return Check(
        "Context has no alert/redeem/control authority",
        check.status,
        check.detail,
    )


def _physical_checklist() -> list[Check]:
    items = [
        "Open Details opens with Current usage and Historical context",
        "Historical context remains visually separate from Current usage",
        "View history still opens the correct History window",
        "History hide/show and period switching remain stable",
        "Current refresh works with History visible",
        "Context absence/insufficient wording is factual and non-predictive",
        "tray/native glance remains usage-only",
        "reset/control/redeem surfaces remain unchanged by Context",
        "Close and reopen Open Details without duplicate/stale widgets",
    ]
    return [Check(item, "MANUAL", "validate on target desktop") for item in items]


def _full_gate() -> list[Check]:
    commands = [
        ["uv", "run", "pytest", "-ra"],
        ["uv", "run", "ruff", "check", "src", "tests", "scripts"],
        ["uv", "run", "mypy"],
        ["uv", "run", "python", "-m", "compileall", "-q", "src", "scripts"],
        ["git", "diff", "--check"],
    ]
    return [_run(command) for command in commands]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CodexBar v1.6 target validation")
    parser.add_argument(
        "--real-read",
        action="store_true",
        help="inspect real history and perform a read-only current-account Context check",
    )
    parser.add_argument(
        "--full-gate",
        action="store_true",
        help="run the complete pytest/ruff/mypy/compileall/diff gate",
    )
    args = parser.parse_args(argv)

    checks = _preflight()
    checks.append(_version_check())
    checks.append(_absence_state_check())
    checks.append(_side_effect_check())

    if args.real_read:
        checks.append(_history_check())
        checks.append(_real_context_check())
    else:
        checks.extend(
            [
                Check(
                    "real history inspect",
                    "SKIP",
                    "run with --real-read on the target desktop",
                ),
                Check(
                    "real CURRENT Context",
                    "SKIP",
                    "run with --real-read when current metadata permits",
                ),
            ]
        )

    if args.full_gate:
        checks.extend(_full_gate())
    else:
        checks.append(
            Check(
                "full global gate",
                "SKIP",
                "run with --full-gate before release closure",
            )
        )

    checks.extend(_physical_checklist())

    print("CodexBar v1.6 validation")
    for check in checks:
        _print(check)

    failures = [check for check in checks if check.status == "FAIL"]
    summary = {
        "pass": sum(check.status == "PASS" for check in checks),
        "skip": sum(check.status == "SKIP" for check in checks),
        "manual": sum(check.status == "MANUAL" for check in checks),
        "fail": len(failures),
    }
    print("SUMMARY " + json.dumps(summary, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
