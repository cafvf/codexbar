from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager
from codexbar.application.settings import SettingsRepository
from codexbar.domain.settings import AppSettings
from codexbar.ui.control_panel import CurrentAccountPanel
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_tray import HistoricalTrayShell


class ControlTrayShell(HistoricalTrayShell):
    def __init__(
        self,
        app: QApplication,
        provider: UsageProvider,
        settings: AppSettings,
        repository: SettingsRepository,
        notifier: NotificationPort,
        history_controller: HistoryController,
        presenter: CurrentAccountPresenter,
        redeem_manager: RedeemProcessManager | None,
    ) -> None:
        self._presenter = presenter
        panel = CurrentAccountPanel(
            presenter,
            redeem_manager,
            on_history=self.show_history_for_window,
            on_redeem_changed=self.refresh,
        )
        super().__init__(
            app,
            provider,
            settings,
            repository,
            notifier,
            history_controller,
            panel=panel,
        )

    def apply_settings(self, settings: AppSettings) -> None:
        super().apply_settings(settings)
        self._presenter.apply_settings(settings)


def run_tray(
    provider: UsageProvider,
    settings: AppSettings,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController,
    presenter: CurrentAccountPresenter,
    redeem_manager: RedeemProcessManager | None,
) -> int:
    instance = QApplication.instance()
    app = instance if isinstance(instance, QApplication) else QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    shell = ControlTrayShell(
        app,
        provider,
        settings,
        repository,
        notifier,
        history_controller,
        presenter,
        redeem_manager,
    )
    shell.start()
    return app.exec()
