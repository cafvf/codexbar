from __future__ import annotations

import argparse
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

DEFAULT_OUTPUT: Final = Path(
    "docs/validation/v1.4-target-validation.md"
)


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True, slots=True)
class ManualCheck:
    title: str
    instruction: str
    required: bool = True


MANUAL_CHECKS: Final = (
    ManualCheck(
        "Rich current panel opens",
        (
            "Launch `uv run codexbar --gui`, open details, and confirm "
            "the enriched CURRENT panel is visible."
        ),
    ),
    ManualCheck(
        "Current cards show expected fields",
        (
            "Confirm each reported window shows label, whole percent, "
            "progress bar, AVAILABLE/LOW/EXHAUSTED state, and reset data "
            "when available."
        ),
    ),
    ManualCheck(
        "CURRENT and STALE are distinguishable",
        (
            "Confirm CURRENT is explicit during normal operation. If a "
            "STALE state is safely reproducible, confirm the last valid "
            "values remain visible and STALE is clearly indicated."
        ),
        required=False,
    ),
    ManualCheck(
        "Observation age updates",
        (
            "Confirm the detail panel shows the observation timestamp and "
            "a plausible elapsed age derived from the current snapshot."
        ),
    ),
    ManualCheck(
        "Reset presentation is coherent",
        (
            "For a window with reset metadata, confirm the Reset text shows "
            "both absolute time and relative duration. If the card says "
            "`Reset: not reported`, mark this check SKIP."
        ),
        required=False,
    ),
    ManualCheck(
        "Current-to-history navigation preserves identity",
        (
            "Click View history on a CURRENT card and confirm History opens "
            "focused on the same usage window, not merely a matching label."
        ),
    ),
    ManualCheck(
        "Current refresh remains responsive",
        (
            "Open History, close/hide it, trigger CURRENT Refresh, then repeat "
            "with History visible. Confirm CodexBar remains running, the current "
            "panel stays responsive, and values update normally."
        ),
    ),
    ManualCheck(
        "History remains functional",
        (
            "Open History and confirm retained observations, 24h/7d/30d period "
            "switching, explicit time-axis semantics, and discrete observations."
        ),
    ),
    ManualCheck(
        "Ayatana path remains functional",
        (
            "Confirm the native Ayatana indicator still shows the canonical "
            "glance and exposes Refresh, Open details, History, Settings, Quit."
        ),
    ),
    ManualCheck(
        "Qt fallback remains functional",
        (
            "When the Qt fallback path is available, confirm tray, details, "
            "History, Settings, Refresh, and Quit remain usable."
        ),
        required=False,
    ),
)


def _run(command: tuple[str, ...]) -> CommandResult:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _ask(check: ManualCheck) -> tuple[str, str]:
    print()
    print(f"[MANUAL] {check.title}")
    print(check.instruction)
    while True:
        answer = input("Result [p=pass, f=fail, s=skip]: ").strip().lower()
        if answer in {"p", "f", "s"}:
            break
        print("Enter p, f, or s.")
    note = input("Note (optional): ").strip()
    status = {"p": "PASS", "f": "FAIL", "s": "SKIP"}[answer]
    return status, note


def _environment_lines() -> list[str]:
    keys = (
        "XDG_CURRENT_DESKTOP",
        "XDG_SESSION_TYPE",
        "DISPLAY",
        "WAYLAND_DISPLAY",
    )
    lines = [
        f"- Platform: `{platform.platform()}`",
        f"- Python: `{platform.python_version()}`",
    ]
    lines.extend(
        f"- {key}: `{os.environ.get(key, '')}`"
        for key in keys
    )
    return lines


def _command_section(title: str, result: CommandResult) -> str:
    command = " ".join(result.command)
    status = "PASS" if result.ok else "FAIL"
    stdout = result.stdout or "(no stdout)"
    stderr = result.stderr or "(no stderr)"
    return "\n".join(
        (
            f"### {title} — {status}",
            "",
            f"`{command}`",
            "",
            "```text",
            stdout,
            "```",
            "",
            "stderr:",
            "",
            "```text",
            stderr,
            "```",
        )
    )


def _write_report(
    path: Path,
    commands: tuple[tuple[str, CommandResult], ...],
    manual_results: tuple[tuple[ManualCheck, str, str], ...],
) -> None:
    now = datetime.now().astimezone()
    command_failures = sum(
        not result.ok for _, result in commands
    )
    manual_failures = sum(
        status == "FAIL" for _, status, _ in manual_results
    )
    required_skips = sum(
        status == "SKIP" and check.required
        for check, status, _ in manual_results
    )

    overall = (
        "PASS"
        if command_failures == 0
        and manual_failures == 0
        and required_skips == 0
        else "INCOMPLETE"
        if command_failures == 0 and manual_failures == 0
        else "FAIL"
    )

    body = [
        "# CodexBar v1.4 — Target Validation",
        "",
        f"Date: {now.isoformat(timespec='seconds')}",
        f"Overall result: **{overall}**",
        "",
        "## Environment",
        "",
        *_environment_lines(),
        "",
        "## Automated preflight",
        "",
    ]

    for title, result in commands:
        body.extend((_command_section(title, result), ""))

    body.extend(("## Manual target-system checks", ""))

    for index, (check, status, note) in enumerate(
        manual_results,
        start=1,
    ):
        requirement = "required" if check.required else "conditional"
        body.append(
            f"{index}. **{status} — {check.title}** ({requirement})"
        )
        body.append(f"   - Procedure: {check.instruction}")
        if note:
            body.append(f"   - Note: {note}")

    body.extend(
        (
            "",
            "## v1.4 target gate",
            "",
            (
                "The v1.4 target gate closes only when automated preflight "
                "is green and all required manual checks pass."
            ),
            (
                "Conditional checks may be skipped when the corresponding "
                "runtime state/path is not safely available, with justification."
            ),
            "",
        )
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run CodexBar v1.4 target-system validation."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
    )
    args = parser.parse_args()

    specs = (
        ("pytest", ("uv", "run", "pytest", "-ra")),
        (
            "ruff",
            ("uv", "run", "ruff", "check", "src", "tests", "scripts"),
        ),
        ("mypy", ("uv", "run", "mypy")),
        (
            "compileall",
            (
                "uv",
                "run",
                "python",
                "-m",
                "compileall",
                "-q",
                "src",
                "scripts",
            ),
        ),
        (
            "history inspect",
            ("uv", "run", "codexbar", "history", "inspect"),
        ),
        (
            "native indicator diagnostics",
            ("uv", "run", "codexbar", "--diagnose-indicator"),
        ),
    )

    commands: list[tuple[str, CommandResult]] = []
    for title, command in specs:
        print(f"[RUN] {title}: {' '.join(command)}")
        result = _run(command)
        commands.append((title, result))
        print(f"      {'PASS' if result.ok else 'FAIL'}")

    manual: list[tuple[ManualCheck, str, str]] = []
    for check in MANUAL_CHECKS:
        if args.non_interactive:
            manual.append((check, "SKIP", "non-interactive run"))
        else:
            status, note = _ask(check)
            manual.append((check, status, note))

    _write_report(args.output, tuple(commands), tuple(manual))
    print()
    print(f"Validation record written to: {args.output}")

    command_failure = any(not result.ok for _, result in commands)
    manual_failure = any(
        status == "FAIL" for _, status, _ in manual
    )
    required_skip = any(
        status == "SKIP" and check.required
        for check, status, _ in manual
    )

    if command_failure or manual_failure:
        return 2
    if required_skip:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
