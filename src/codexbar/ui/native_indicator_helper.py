#!/usr/bin/python3
"""System-Python Ayatana helper for CodexBar.

This module intentionally uses only the Python standard library plus the distro-provided
PyGObject bindings. It is executed directly with /usr/bin/python3 and communicates with
the uv-managed CodexBar process using JSON Lines over stdin/stdout.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
import threading
from contextlib import suppress
from pathlib import Path
from typing import Any

MENU_ACTIONS = (
    ("Refresh", "refresh"),
    ("Open details", "details"),
    ("Settings", "settings"),
    ("Quit", "quit"),
)

_DIAGNOSTIC_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _emit(event: str) -> None:
    print(json.dumps({"event": event}, separators=(",", ":")), flush=True)


def _emit_diagnostic(step: str, ok: bool, detail: str | None = None) -> None:
    payload: dict[str, Any] = {"type": "diagnostic", "step": step, "ok": ok}
    if detail is not None:
        payload["detail"] = detail
    print(json.dumps(payload, separators=(",", ":")), flush=True)


def _load_bindings() -> tuple[Any, Any, Any]:
    import gi

    gi.require_version("AyatanaAppIndicator3", "0.1")
    gi.require_version("Gtk", "3.0")
    from gi.repository import AyatanaAppIndicator3, GLib, Gtk

    return AyatanaAppIndicator3, GLib, Gtk


def _reader(GLib: Any, apply_command: Any) -> None:
    for raw in sys.stdin:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        GLib.idle_add(apply_command, message)
    GLib.idle_add(apply_command, {"command": "quit"})


def _run_diagnostics() -> int:
    environment_detail = (
        f"desktop={os.environ.get('XDG_CURRENT_DESKTOP', '')}; "
        f"session={os.environ.get('XDG_SESSION_TYPE', '')}; "
        f"display={bool(os.environ.get('DISPLAY'))}; "
        f"wayland={bool(os.environ.get('WAYLAND_DISPLAY'))}"
    )
    _emit_diagnostic("environment", True, environment_detail)
    try:
        import gi
    except Exception as exc:
        _emit_diagnostic("gi-import", False, repr(exc))
        return 10
    _emit_diagnostic("gi-import", True, getattr(gi, "__file__", None))

    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3
    except Exception as exc:
        _emit_diagnostic("ayatana-import", False, repr(exc))
        return 11
    _emit_diagnostic("ayatana-import", True)

    try:
        gi.require_version("Gtk", "3.0")
        from gi.repository import GLib, Gtk
    except Exception as exc:
        _emit_diagnostic("gtk-import", False, repr(exc))
        return 12
    _emit_diagnostic("gtk-import", True)

    with tempfile.TemporaryDirectory(prefix="codexbar-indicator-diagnostic-") as tmp:
        icon = Path(tmp) / "codexbar.png"
        icon.write_bytes(_DIAGNOSTIC_PNG)
        try:
            indicator = AyatanaAppIndicator3.Indicator.new_with_path(
                "codexbar-diagnostic",
                icon.stem,
                AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
                str(icon.parent),
            )
            indicator.set_title("CodexBar diagnostic")
        except Exception as exc:
            _emit_diagnostic("indicator-create", False, repr(exc))
            return 13
        _emit_diagnostic("indicator-create", True)

        try:
            menu = Gtk.Menu()
            summary = Gtk.MenuItem(label="CodexBar diagnostic")
            summary.set_sensitive(False)
            menu.append(summary)
            menu.append(Gtk.SeparatorMenuItem())
            quit_item = Gtk.MenuItem(label="Quit diagnostic")
            menu.append(quit_item)
            menu.show_all()
            indicator.set_menu(menu)
        except Exception as exc:
            _emit_diagnostic("menu-bind", False, repr(exc))
            return 14
        _emit_diagnostic("menu-bind", True)

        try:
            indicator.set_label("5h: 99% · W: 88%", "5h: 100% · W: 100% · stale")
        except Exception as exc:
            _emit_diagnostic("label-set", False, repr(exc))
            return 15
        _emit_diagnostic("label-set", True)

        try:
            indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        except Exception as exc:
            _emit_diagnostic("status-active", False, repr(exc))
            return 16
        _emit_diagnostic("status-active", True)

        try:
            loop = GLib.MainLoop()
            GLib.timeout_add(250, lambda: (loop.quit(), False)[1])
            loop.run()
        except Exception as exc:
            _emit_diagnostic("glib-loop", False, repr(exc))
            return 17
        finally:
            with suppress(Exception):
                indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE)
        _emit_diagnostic(
            "glib-loop",
            True,
            "250 ms loop completed; physical shell rendering is not asserted",
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icon")
    parser.add_argument("--diagnose", action="store_true")
    args = parser.parse_args()

    if args.diagnose:
        return _run_diagnostics()
    if not args.icon:
        parser.error("--icon is required unless --diagnose is used")

    icon = Path(args.icon)
    if not icon.is_file():
        print(json.dumps({"error": "icon-not-found"}), flush=True)
        return 2

    try:
        AppIndicator3, GLib, Gtk = _load_bindings()
    except (ImportError, ValueError) as exc:
        print(json.dumps({"error": "bindings-unavailable", "detail": str(exc)}), flush=True)
        return 3

    indicator = AppIndicator3.Indicator.new_with_path(
        "codexbar",
        icon.stem,
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        str(icon.parent),
    )
    indicator.set_title("CodexBar")

    menu = Gtk.Menu()
    summary_item = Gtk.MenuItem(label="Loading usage…")
    summary_item.set_sensitive(False)
    menu.append(summary_item)
    menu.append(Gtk.SeparatorMenuItem())

    refresh_item = Gtk.MenuItem(label="Refresh")
    refresh_item.connect("activate", lambda *_: _emit("refresh"))
    menu.append(refresh_item)

    details_item = Gtk.MenuItem(label="Open details")
    details_item.connect("activate", lambda *_: _emit("details"))
    menu.append(details_item)

    settings_item = Gtk.MenuItem(label="Settings")
    settings_item.connect("activate", lambda *_: _emit("settings"))
    menu.append(settings_item)

    menu.append(Gtk.SeparatorMenuItem())
    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda *_: _emit("quit"))
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    loop = GLib.MainLoop()

    def apply_command(message: dict[str, Any]) -> bool:
        command = message.get("command")
        if command == "set_glance":
            text = str(message.get("text", ""))
            guide = str(message.get("guide", ""))
            indicator.set_label(text, guide)
            summary_item.set_label(text)
        elif command == "quit":
            indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
            loop.quit()
        return False

    threading.Thread(target=_reader, args=(GLib, apply_command), daemon=True).start()
    _emit("ready")
    loop.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
