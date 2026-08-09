from __future__ import annotations

from collections.abc import Callable

from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.settings import GetSettings, SettingsRepository
from codexbar.domain.settings import AppSettings
from codexbar.ui.errors import GuiDependencyError

QtTrayRunner = Callable[
    [UsageProvider, AppSettings, SettingsRepository, NotificationPort],
    int,
]


def _load_qt_tray() -> QtTrayRunner:
    try:
        from codexbar.ui.tray import run_tray as run_qt_tray
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            raise GuiDependencyError(
                "PySide6 is required for the tray UI; install with "
                "`uv sync --extra gui --extra dev`"
            ) from exc
        raise
    return run_qt_tray


def run_tray(
    provider: UsageProvider,
    *,
    repository: SettingsRepository,
    notifier: NotificationPort,
) -> int:
    settings = GetSettings(repository).execute().settings
    return _load_qt_tray()(provider, settings, repository, notifier)
