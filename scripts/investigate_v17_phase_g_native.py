#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture Phase G Ayatana/canberra diagnostic evidence."
    )
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    completed = subprocess.run(
        [sys.executable, "-m", "codexbar", "--diagnose-indicator"],
        text=True,
        capture_output=True,
        check=False,
    )

    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    canberra_seen = "canberra" in combined
    ayatana_deprecation_seen = "ayatana" in combined and "deprecat" in combined

    payload = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "diagnostic_exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "canberra_warning_seen": canberra_seen,
        "ayatana_deprecation_seen": ayatana_deprecation_seen,
        "classification": {
            "canberra": (
                "non_blocking_warning_candidate"
                if canberra_seen and completed.returncode == 0
                else "not_observed_or_requires_review"
            ),
            "ayatana": (
                "migration_candidate_requires_separate_prototype_and_physical_gate"
                if ayatana_deprecation_seen
                else "retain_validated_backend"
            ),
        },
        "policy": (
            "This capture never installs dependencies or changes the native backend. "
            "Physical GNOME/Ayatana rendering evidence remains separate."
        ),
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    print(encoded)

    if args.json_out is not None:
        args.json_out.write_text(encoded + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
