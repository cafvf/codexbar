from __future__ import annotations

from collections.abc import Callable

from codexbar.application.instance_ownership import InstanceOwnerBinding, InstanceResolution
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager
from codexbar.application.settings import GetSettings, SettingsRepository
from codexbar.domain.settings import AppSettings
from codexbar.ui.context_viewmodel import ContextPresenter
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter
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
ControlQtTrayRunner = Callable[
    [
        UsageProvider,
        AppSettings,
        SettingsRepository,
        NotificationPort,
        HistoryController,
        CurrentAccountPresenter,
        RedeemProcessManager | None,
        ContextPresenter | None,
        InstanceOwnerBinding | None,
    ],
    int,
]


def _load_qt_tray() -> QtTrayRunner:
    try:
        from codexbar.ui.tray import run_tray
    except ModuleNotFoundError as exc:
        _normalize_qt_import_error(exc)
        raise
    return run_tray


def _load_historical_qt_tray() -> HistoricalQtTrayRunner:
    try:
        from codexbar.ui.history_tray import run_tray
    except ModuleNotFoundError as exc:
        _normalize_qt_import_error(exc)
        raise
    return run_tray


def _load_control_qt_tray() -> ControlQtTrayRunner:
    try:
        from codexbar.ui.control_tray import run_tray
    except ModuleNotFoundError as exc:
        _normalize_qt_import_error(exc)
        raise
    return run_tray


def resolve_gui_instance() -> InstanceResolution:
    try:
        from codexbar.ui.instance_ownership import resolve_gui_instance as resolve
    except ModuleNotFoundError as exc:
        _normalize_qt_import_error(exc)
        raise
    return resolve()


def _normalize_qt_import_error(exc: ModuleNotFoundError) -> None:
    if exc.name and exc.name.startswith("PySide6"):
        raise GuiDependencyError(
            "PySide6 is required for the tray UI; install with "
            "`uv sync --extra gui --extra dev`"
        ) from exc


def run_tray(
    provider: UsageProvider,
    *,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController | None = None,
    presenter: CurrentAccountPresenter | None = None,
    redeem_manager: RedeemProcessManager | None = None,
    context_presenter: ContextPresenter | None = None,
    instance_owner: InstanceOwnerBinding | None = None,
) -> int:
    settings = GetSettings(repository).execute().settings

    if history_controller is not None and presenter is not None:
        return _load_control_qt_tray()(
            provider,
            settings,
            repository,
            notifier,
            history_controller,
            presenter,
            redeem_manager,
            context_presenter,
            instance_owner,
        )

    if instance_owner is not None:
        raise RuntimeError("instance ownership requires the composed v1.6+ control tray")

    if history_controller is not None:
        return _load_historical_qt_tray()(
            provider,
            settings,
            repository,
            notifier,
            history_controller,
        )

    return _load_qt_tray()(
        provider,
        settings,
        repository,
        notifier,
    )
