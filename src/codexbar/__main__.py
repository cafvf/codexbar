from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from codexbar.application.history import HistoryError, HistoryState
from codexbar.application.history_runtime import HistoryCapturingUsageProvider, HistoryService
from codexbar.application.ports import UsageProvider
from codexbar.application.reset_ledger_cli import print_reset_ledger_inspection
from codexbar.application.settings import GetSettings, ResetSettings, SettingsLoadResult
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.composition import build_gui_runtime, build_usage_provider
from codexbar.domain.errors import CodexBarError, SettingsError
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository
from codexbar.infrastructure.settings import JsonSettingsRepository
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

    settings = subparsers.add_parser(
        "settings",
        help="inspect or reset persistent CodexBar settings",
    )
    settings_sub = settings.add_subparsers(dest="settings_command", required=True)
    settings_sub.add_parser("show", help="show effective settings and their origin")
    settings_sub.add_parser("reset", help="reset persistent settings to defaults")

    history = subparsers.add_parser(
        "history",
        help="inspect or clear persistent CodexBar usage history",
    )
    history_sub = history.add_subparsers(dest="history_command", required=True)
    history_sub.add_parser("inspect", help="inspect local usage-history storage")
    history_sub.add_parser(
        "clear",
        help="destructively clear all stored usage history while preserving the schema",
    )

    reset_ledger = subparsers.add_parser(
        "reset-ledger",
        help="inspect persistent reset-credit evidence storage",
    )
    reset_ledger_sub = reset_ledger.add_subparsers(dest="reset_ledger_command", required=True)
    reset_ledger_sub.add_parser("inspect", help="inspect local reset-credit event ledger")
    return parser


def _format_percent(value: Decimal) -> str:
    percent = value * Decimal("100")
    return format(percent.normalize(), "f")


def _print_settings(result: SettingsLoadResult) -> None:
    settings = result.settings
    print(f"Origin: {result.origin.value}")
    print(
        "LOW remaining threshold: "
        f"{_format_percent(settings.low_remaining_threshold.value)}%"
    )
    print(f"Refresh interval: {settings.refresh_interval_seconds.value} seconds")
    notifications = "enabled" if settings.notifications_enabled else "disabled"
    print(f"Notifications: {notifications}")
    print(f"Settings schema source: {result.source_schema_version or 'defaults'}")
    if not settings.usage_reserves.entries:
        print("Usage reserves: none")
    else:
        print("Usage reserves:")
        for entry in settings.usage_reserves.entries:
            print(f"  {entry.window_id.value}: {_format_percent(entry.reserve.value)}%")
    if result.diagnostic is not None:
        print(f"Diagnostic: {result.diagnostic}")


def _run_settings(command: str) -> int:
    repository = JsonSettingsRepository()
    try:
        if command == "show":
            _print_settings(GetSettings(repository).execute())
            return 0
        if command == "reset":
            ResetSettings(repository).execute()
            print("Settings reset to defaults.")
            return 0
    except SettingsError as exc:
        print(f"CodexBar: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unsupported settings command: {command}")


def _print_history_inspection() -> int:
    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    print(f"Path: {inspection.path}")
    print(f"State: {inspection.state.value}")
    if inspection.schema_version is not None:
        print(f"Schema: {inspection.schema_version}")
    if inspection.snapshot_count is not None:
        print(f"Snapshots: {inspection.snapshot_count}")
    if inspection.oldest_observed_at is not None:
        print(f"Oldest: {inspection.oldest_observed_at.isoformat()}")
    if inspection.newest_observed_at is not None:
        print(f"Newest: {inspection.newest_observed_at.isoformat()}")
    if inspection.diagnostic is not None:
        print(f"Diagnostic: {inspection.diagnostic}")
    return 2 if inspection.state in {HistoryState.UNREADABLE, HistoryState.UNSUPPORTED} else 0


def _clear_history() -> int:
    path = history_database_path()
    inspection = SqliteHistoryRepository.inspect_path(path)
    if inspection.state is HistoryState.ABSENT:
        print("History already empty (database absent).")
        return 0
    if inspection.state in {HistoryState.UNREADABLE, HistoryState.UNSUPPORTED}:
        print(
            f"CodexBar: cannot clear history in state {inspection.state.value}: "
            f"{inspection.diagnostic or 'unknown history error'}",
            file=sys.stderr,
        )
        return 2
    try:
        SqliteHistoryRepository(path).clear()
    except HistoryError as exc:
        print(f"CodexBar: {exc}", file=sys.stderr)
        return 2
    print("Usage history cleared.")
    return 0


def _run_history(command: str) -> int:
    if command == "inspect":
        return _print_history_inspection()
    if command == "clear":
        return _clear_history()
    raise AssertionError(f"unsupported history command: {command}")


def _run_desktop(args: argparse.Namespace) -> int:
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
    raise AssertionError("unsupported desktop command")


def _run_indicator_diagnostics() -> int:
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


def _with_history(provider: UsageProvider) -> UsageProvider:
    try:
        repository = SqliteHistoryRepository(history_database_path())
    except HistoryError as exc:
        print(f"CodexBar history disabled: {exc}", file=sys.stderr)
        return provider
    return HistoryCapturingUsageProvider(provider, HistoryService(repository))


def _print_usage(provider: UsageProvider) -> int:
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "desktop":
        return _run_desktop(args)
    if args.command == "settings":
        return _run_settings(args.settings_command)
    if args.command == "history":
        return _run_history(args.history_command)
    if args.command == "reset-ledger":
        if args.reset_ledger_command == "inspect":
            return print_reset_ledger_inspection()
        raise AssertionError(f"unsupported reset-ledger command: {args.reset_ledger_command}")
    if args.diagnose_indicator:
        return _run_indicator_diagnostics()

    if args.gui:
        try:
            from codexbar.ui.launcher import run_tray

            runtime = build_gui_runtime(mock=args.mock)
            try:
                return run_tray(
                    runtime.provider,
                    repository=runtime.settings_repository,
                    notifier=runtime.notifier,
                    history_controller=runtime.history_controller,
                    presenter=runtime.presenter,
                    redeem_manager=runtime.redeem_manager,
                    context_presenter=runtime.context_presenter,
                )
            finally:
                runtime.close()
        except CodexBarError as exc:
            print(f"CodexBar: {exc}", file=sys.stderr)
            return 2

    provider = _with_history(build_usage_provider(mock=args.mock))
    return _print_usage(provider)


if __name__ == "__main__":
    raise SystemExit(main())
