from __future__ import annotations

from collections.abc import Callable

from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.settings import GetSettings, SettingsRepository
from codexbar.domain.settings import AppSettings
from codexbar.ui.errors import GuiDependencyError
from codexbar.ui.history_controller import HistoryController

QtTrayRunner = Callable[
    [UsageProvider, AppSettings, SettingsRepository, NotificationPort],
    int,
]

HistoricalQtTrayRunner = Callable[
    [
        UsageProvider,
        AppSettings,
        SettingsRepository,
        NotificationPort,
        HistoryController,
    ],
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


def _load_historical_qt_tray() -> HistoricalQtTrayRunner:
    try:
        from codexbar.ui.history_tray import run_tray as run_historical_tray
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            raise GuiDependencyError(
                "PySide6 is required for the tray UI; install with "
                "`uv sync --extra gui --extra dev`"
            ) from exc
        raise
    return run_historical_tray


def run_tray(
    provider: UsageProvider,
    *,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController | None = None,
) -> int:
    settings = GetSettings(repository).execute().settings
    if history_controller is None:
        return _load_qt_tray()(provider, settings, repository, notifier)
    return _load_historical_qt_tray()(
        provider,
        settings,
        repository,
        notifier,
        history_controller,
    )
