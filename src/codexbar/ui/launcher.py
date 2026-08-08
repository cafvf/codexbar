from __future__ import annotations

from codexbar.application.ports import UsageProvider
from codexbar.ui.controller import DEFAULT_TRAY_SETTINGS, TraySettings
from codexbar.ui.errors import GuiDependencyError


def run_tray(provider: UsageProvider, settings: TraySettings = DEFAULT_TRAY_SETTINGS) -> int:
    try:
        from codexbar.ui.tray import run_tray as run_qt_tray
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            raise GuiDependencyError(
                "PySide6 is required for the tray UI; install with "
                "`uv sync --extra gui --extra dev`"
            ) from exc
        raise
    return run_qt_tray(provider, settings)
