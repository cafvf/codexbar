from __future__ import annotations

from datetime import datetime
from pathlib import Path

OUTPUT = Path("docs/validation/PHASE-E-CONTEXT-UI-SMOKE.local.md")

CHECKS = (
    (
        "Historical context is visibly separate from authoritative Current",
        "AC-1615 / TASK-651",
    ),
    (
        "Each Current window has exactly one View history button",
        "v1.4 navigation contract",
    ),
    (
        "5 hours mock shows Sparse coverage and observed historical range",
        "TASK-653",
    ),
    (
        "Weekly mock shows Established coverage, median, middle 50%, and rank",
        "TASK-655",
    ),
    (
        "Weekly rank explicitly reports equal values when ties exist",
        "TASK-656",
    ),
    (
        "Comparable-cycle count is visible for both mock windows",
        "AC-1615 / TASK-652..655",
    ),
    (
        "Current detail cards explicitly label their percentages as left",
        "TASK-657 / existing UI semantics",
    ),
    (
        "Tray/native glance remains compact and usage-only",
        "TASK-657 / frozen UI contract",
    ),
    (
        "Usage History opens from each Current window and refreshes normally",
        "TASK-658",
    ),
)


def _answer(prompt: str) -> tuple[bool, str]:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True, input("Observation (optional): ").strip()
        if answer in {"n", "no"}:
            return False, input("Describe the problem: ").strip()
        print("Please answer y or n.")


def main() -> int:
    print("CodexBar v1.6 Phase E — physical UI smoke")
    print("Keep `uv run python -m codexbar --gui --mock` running in another terminal.")
    print("Open details and exercise View history for both Current windows.")
    print(
        "Limited coverage and predictive-language exclusions are verified by "
        "automated tests, not by this physical smoke.\n"
    )

    results = []
    for description, trace in CHECKS:
        ok, note = _answer(description)
        results.append((description, trace, ok, note))

    passed = all(item[2] for item in results)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CodexBar v1.6 Phase E — Physical UI Smoke",
        "",
        f"Recorded: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        "",
        "| Check | Trace | Result | Observation |",
        "|---|---|---|---|",
    ]
    for description, trace, ok, note in results:
        safe_note = note.replace("|", "\\|")
        lines.append(
            f"| {description} | {trace} | {'PASS' if ok else 'FAIL'} | {safe_note} |"
        )
    lines.append("")
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{'PASS' if passed else 'FAIL'}")
    print(f"Observations written to: {OUTPUT}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
