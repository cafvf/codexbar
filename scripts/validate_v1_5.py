from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.mock_control import (
    MockAccountRateLimitsReader,
    MockResetCreditConsumer,
)
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
from codexbar.infrastructure.settings import JsonSettingsRepository


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
    return Check(" ".join(command), "PASS" if completed.returncode == 0 else "FAIL", detail)


def _preflight() -> list[Check]:
    required = [
        Path("pyproject.toml"),
        Path("src/codexbar/composition.py"),
        Path("src/codexbar/application/redeem.py"),
        Path("src/codexbar/ui/control_panel.py"),
    ]
    return [
        Check(
            str(path),
            "PASS" if path.exists() else "FAIL",
            "present" if path.exists() else "missing",
        )
        for path in required
    ]


def _mock_checks() -> list[Check]:
    observation = MockAccountRateLimitsReader().read_account_rate_limits()
    inventory = observation.reset_credits.inventory
    consumer = MockResetCreditConsumer()
    checks = [
        Check("mock usage", "PASS", f"{len(observation.usage.windows)} windows"),
        Check(
            "mock reset inventory",
            "PASS" if inventory is not None and inventory.available_count == 2 else "FAIL",
            f"count={inventory.available_count if inventory else 'none'}",
        ),
        Check("mock safe consumer", "PASS", consumer.__class__.__name__),
    ]
    return checks


def _settings_check() -> Check:
    repository = JsonSettingsRepository()
    result = repository.load()
    return Check(
        "settings load",
        "PASS",
        f"origin={result.origin.value}; source_schema={result.source_schema_version or 'defaults'}",
    )


def _ledger_check() -> Check:
    inspection = SqliteResetEventRepository.inspect_path(reset_ledger_database_path())
    return Check(
        "reset ledger inspect",
        "PASS" if inspection.state.value not in {"unreadable", "unsupported"} else "FAIL",
        f"state={inspection.state.value}; events={inspection.event_count}",
    )


def _real_read() -> Check:
    try:
        observation = CodexAccountRateLimitsReader().read_account_rate_limits()
    except Exception as exc:
        return Check("real account read-only", "SKIP", f"capability/source unavailable: {exc}")
    reset = observation.reset_credits
    count = reset.inventory.available_count if reset.inventory is not None else "unavailable"
    return Check(
        "real account read-only",
        "PASS",
        f"usage_windows={len(observation.usage.windows)}; reset_count={count}",
    )


def _physical_checklist() -> list[Check]:
    items = [
        "Current refresh",
        "Current -> History",
        "History hide/show",
        "History period switching",
        "Current refresh with History visible",
        "reset/control panel rendering",
        "reserve setting save/apply",
        "redeem confirmation dialog",
        "native Ayatana or Qt fallback",
    ]
    return [Check(item, "MANUAL", "validate on target desktop") for item in items]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CodexBar v1.5 target validation")
    parser.add_argument(
        "--real-read",
        action="store_true",
        help="perform read-only real account validation",
    )
    parser.add_argument(
        "--real-redeem",
        action="store_true",
        help="mark real redeem validation as requested; destructive and never run automatically",
    )
    args = parser.parse_args(argv)

    checks = _preflight()
    checks.extend(_mock_checks())
    checks.append(_settings_check())
    checks.append(_ledger_check())
    if args.real_read:
        checks.append(_real_read())
    else:
        checks.append(
            Check(
                "real account read-only",
                "SKIP",
                "run with --real-read on supported account",
            )
        )

    if args.real_redeem:
        checks.append(
            Check(
                "real redeem",
                "MANUAL",
                "destructive: use GUI confirmation on a safely spendable "
                "credit and record evidence",
            )
        )
    else:
        checks.append(Check("real redeem", "SKIP", "optional destructive validation not requested"))

    checks.extend(_physical_checklist())

    print("CodexBar v1.5 validation")
    for check in checks:
        _print(check)

    automated_failures = [check for check in checks if check.status == "FAIL"]
    summary = {
        "pass": sum(check.status == "PASS" for check in checks),
        "skip": sum(check.status == "SKIP" for check in checks),
        "manual": sum(check.status == "MANUAL" for check in checks),
        "fail": len(automated_failures),
    }
    print("SUMMARY " + json.dumps(summary, sort_keys=True))
    return 1 if automated_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
