#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess


def main() -> int:
    executable = shutil.which("notify-send")
    print("CodexBar notification diagnostics")
    print(f"notify-send path: {executable!r}")
    if executable is None:
        print("FAILED: notify-send not found. Install libnotify-bin.")
        return 2

    completed = subprocess.run(
        [
            executable,
            "--app-name=CodexBar",
            "--urgency=normal",
            "--print-id",
            "CodexBar diagnostic",
            "If this appears, libnotify transport is working.",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    print(f"return code: {completed.returncode}")
    print(f"stdout: {completed.stdout.strip()!r}")
    print(f"stderr: {completed.stderr.strip()!r}")
    if completed.returncode != 0:
        return 3

    output = completed.stdout.strip()
    if output and not output.isdigit():
        print("FAILED: --print-id returned a non-numeric notification id.")
        return 4
    if output:
        print(f"accepted notification id: {output}")
    print("PASS: notify-send returned success.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
