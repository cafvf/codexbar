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
        "--diagnose-indicator",
        action="store_true",
        help="diagnose the optional system-Python/Ayatana indicator backend and exit",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="run the Linux system-tray interface instead of the one-shot CLI output",
    )
    subparsers = parser.add_subparsers(dest="command")
    desktop = subparsers.add_parser("desktop", help="manage user-local Linux desktop integration")
    desktop_sub = desktop.add_subparsers(dest="desktop_command", required=True)
    desktop_sub.add_parser("install", help="install the .desktop entry and project icon")
    desktop_sub.add_parser("status", help="show desktop integration status")
    desktop_sub.add_parser("uninstall", help="remove CodexBar-owned desktop integration files")
    autostart = desktop_sub.add_parser("autostart", help="manage opt-in session autostart")
    autostart_sub = autostart.add_subparsers(dest="autostart_command", required=True)
    autostart_sub.add_parser("enable", help="enable user-session autostart")
    autostart_sub.add_parser("disable", help="disable user-session autostart")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "desktop":
        from codexbar.desktop import (
            DesktopIntegrationError,
            desktop_status,
            disable_autostart,
            enable_autostart,
            install_desktop,
            uninstall_desktop,
        )

        try:
            if args.desktop_command == "install":
                paths = install_desktop()
                print(f"Desktop entry: {paths.application_entry}")
                print(f"Icon: {paths.icon}")
                print("Autostart: disabled (opt-in)")
                return 0
            if args.desktop_command == "status":
                status = desktop_status()
                print(f"Installed: {'yes' if status.installed else 'no'}")
                print(f"Launcher: {'ok' if status.launcher_exists else 'missing'}")
                print(f"Desktop entry: {'ok' if status.application_installed else 'missing'}")
                print(f"Icon: {'ok' if status.icon_installed else 'missing'}")
                print(f"Autostart: {'enabled' if status.autostart_enabled else 'disabled'}")
                return 0 if status.installed else 1
            if args.desktop_command == "uninstall":
                uninstall_desktop()
                print("CodexBar desktop integration removed.")
                print("To remove the application tool itself: uv tool uninstall codexbar")
                return 0
            if args.desktop_command == "autostart":
                if args.autostart_command == "enable":
                    path = enable_autostart()
                    print(f"Autostart enabled: {path}")
                    return 0
                if args.autostart_command == "disable":
                    removed = disable_autostart()
                    print("Autostart disabled." if removed else "Autostart already disabled.")
                    return 0
        except DesktopIntegrationError as exc:
            print(f"CodexBar: {exc}", file=sys.stderr)
            return 2

    if args.diagnose_indicator:
        from codexbar.ui.native_indicator import run_indicator_diagnostics

        report = run_indicator_diagnostics()
        print("CodexBar native indicator diagnostics")
        for step in report.steps:
            marker = "PASS" if step.ok else "FAIL"
            detail = f" — {step.detail}" if step.detail else ""
            print(f"[{marker}] {step.name}{detail}")
        if report.stderr:
            print(f"[stderr] {report.stderr}", file=sys.stderr)
        if report.ok:
            print(
                "Result: native indicator API path completed; "
                "physical shell rendering still requires visual validation."
            )
            return 0
        print(
            "Result: native indicator diagnostic failed; Qt fallback should be used.",
            file=sys.stderr,
        )
        return report.exit_code or 2

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
