#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.settings import JsonSettingsRepository


@dataclass(frozen=True, slots=True)
class CommandResult:
    name: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    ok: bool
    detail: str = ""


def _run(name: str, argv: list[str]) -> CommandResult:
    completed = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        name=name,
        argv=tuple(argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        ok=completed.returncode == 0,
    )


def _canonical_persistent_targets() -> tuple[Path, ...]:
    settings_path = JsonSettingsRepository().path
    data_root = history_database_path().parent
    return settings_path, data_root


def _digest_file(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    stat = path.stat()
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": stat.st_size,
    }


def _snapshot_target(
    target: Path,
    snapshot: dict[str, dict[str, object]],
) -> None:
    if not target.exists():
        snapshot[str(target)] = {"state": "absent"}
        return

    if target.is_file():
        try:
            snapshot[str(target)] = _digest_file(target)
        except FileNotFoundError:
            snapshot[str(target)] = {"state": "vanished_during_snapshot"}
        return

    files = sorted(item for item in target.rglob("*") if item.is_file())
    if not files:
        snapshot[str(target)] = {"state": "empty_directory"}
        return
    for path in files:
        try:
            snapshot[str(path)] = _digest_file(path)
        except FileNotFoundError:
            snapshot[str(path)] = {"state": "vanished_during_snapshot"}


def _snapshot_persistent_state() -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    for target in _canonical_persistent_targets():
        _snapshot_target(target, snapshot)
    return snapshot


def _doctor_json_check(result: CommandResult) -> tuple[bool, str]:
    if not result.ok:
        return False, f"doctor --json exit={result.returncode}"
    try:
        payload: Any = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return False, f"invalid doctor JSON: {exc}"
    if not isinstance(payload, dict):
        return False, "doctor JSON root is not an object"
    if payload.get("diagnostics_schema_version") != 1:
        return False, "diagnostics_schema_version is not 1"

    serialized = json.dumps(payload, sort_keys=True).lower()
    forbidden = (
        "access_token",
        "refresh_token",
        "authorization:",
        "bearer ",
        "sk-",
    )
    leaked = [marker for marker in forbidden if marker in serialized]
    if leaked:
        return False, f"forbidden diagnostic marker(s): {', '.join(leaked)}"
    if re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", serialized):
        return False, "doctor JSON contains an email-like value"
    return True, ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run CodexBar v1.7 Phase H real read-only validation."
    )
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    python = sys.executable

    before = _snapshot_persistent_state()

    doctor_text = _run(
        "doctor-text",
        [python, "-m", "codexbar", "doctor"],
    )
    doctor_json = _run(
        "doctor-json",
        [python, "-m", "codexbar", "doctor", "--json"],
    )

    after = _snapshot_persistent_state()
    read_only_ok = before == after
    doctor_json_ok, doctor_json_detail = _doctor_json_check(doctor_json)

    commands = [
        doctor_text,
        doctor_json,
        _run(
            "history-inspect",
            [python, "-m", "codexbar", "history", "inspect"],
        ),
        _run(
            "reset-ledger-inspect",
            [python, "-m", "codexbar", "reset-ledger", "inspect"],
        ),
        _run(
            "desktop-status",
            [python, "-m", "codexbar", "desktop", "status"],
        ),
        _run(
            "version-modes",
            [python, "scripts/validate_v17_version_modes.py"],
        ),
    ]

    checks = {
        "doctor_text_exit": doctor_text.ok,
        "doctor_json_contract": doctor_json_ok,
        "doctor_read_only_persistent_state": read_only_ok,
        "history_inspect_exit": commands[2].ok,
        "reset_ledger_inspect_exit": commands[3].ok,
        "desktop_status_exit": commands[4].ok,
        "version_modes_exit": commands[5].ok,
    }

    payload = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "checks": checks,
        "doctor_json_detail": doctor_json_detail,
        "persistent_targets": [
            str(target) for target in _canonical_persistent_targets()
        ],
        "persistent_state_before": before,
        "persistent_state_after": after,
        "commands": [asdict(item) for item in commands],
        "overall_pass": all(checks.values()),
    }

    encoded = json.dumps(payload, indent=2, sort_keys=True)
    print(encoded)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded + "\n", encoding="utf-8")

    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
