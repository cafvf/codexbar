from __future__ import annotations

import argparse
import sys

from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.errors import CodexBarError
from codexbar.infrastructure.app_server import CodexAppServerProvider
from codexbar.infrastructure.mock_provider import MockUsageProvider
from codexbar.ui.viewmodel import UsageViewModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show current Codex usage limits.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="use deterministic demonstration data instead of the local Codex app-server",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="run the Linux system-tray interface instead of the one-shot CLI output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    provider = MockUsageProvider() if args.mock else CodexAppServerProvider()

    if args.gui:
        try:
            from codexbar.ui.launcher import run_tray

            return run_tray(provider)
        except CodexBarError as exc:
            print(f"CodexBar: {exc}", file=sys.stderr)
            return 2

    try:
        snapshot = GetCurrentUsage(provider).execute()
    except CodexBarError as exc:
        print(f"CodexBar: {exc}", file=sys.stderr)
        return 2

    state = UsageViewModel.from_snapshot(snapshot)
    suffix = " [STALE]" if state.stale else ""
    print(f"CodexBar{suffix}")
    if not state.windows:
        print("No usage windows reported by Codex.")
    for window in state.windows:
        reset = (
            f"; resets {window.reset_at.astimezone().isoformat(timespec='minutes')}"
            if window.reset_at
            else ""
        )
        print(f"{window.label}: {window.percent_left}% left{reset}")
    if state.rate_limit_reached_type:
        print(f"Backend limit state: {state.rate_limit_reached_type}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
