from __future__ import annotations

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.settings import SettingsRepository
from codexbar.domain.models import UsageWindowId
from codexbar.domain.settings import AppSettings
from codexbar.ui.controller import TrayPhase, TrayViewState
from codexbar.ui.current_panel import RichUsagePanel
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_dialog import HistoryDialog
from codexbar.ui.native_indicator import AyatanaHelperIndicator
from codexbar.ui.tray import TrayShell, UsagePanel


class HistoricalTrayShell(TrayShell):
    def __init__(
        self,
        app: QApplication,
        provider: UsageProvider,
        settings: AppSettings,
        repository: SettingsRepository,
        notifier: NotificationPort,
        history_controller: HistoryController,
        *,
        panel: UsagePanel | None = None,
    ) -> None:
        self._history_controller = history_controller
        self._history_dialog: HistoryDialog | None = None
        selected_panel = panel or RichUsagePanel(on_history=self.show_history_for_window)
        super().__init__(
            app,
            provider,
            settings,
            repository,
            notifier,
            panel=selected_panel,
        )
        self._bind_native_history_action()
        self._install_history_menu_action()

    def _install_history_menu_action(self) -> None:
        history_action = QAction("Usage history", self._menu)
        history_action.triggered.connect(self.show_history)
        settings_action = next(
            (action for action in self._menu.actions() if action.text() == "Settings"),
            None,
        )
        if settings_action is None:
            self._menu.addAction(history_action)
        else:
            self._menu.insertAction(settings_action, history_action)

    def _bind_native_history_action(self) -> None:
        native_indicator = self._native_indicator
        if isinstance(native_indicator, AyatanaHelperIndicator):
            native_indicator._callbacks["history"] = self.show_history

    def _on_controller_transition(
        self,
        previous: TrayViewState,
        current: TrayViewState,
    ) -> None:
        if previous.phase is not TrayPhase.LOADING or current.phase is not TrayPhase.FRESH:
            return
        dialog = self._history_dialog
        if dialog is not None and dialog.isVisible():
            dialog.refresh()

    def show_history(self) -> None:
        self._show_history_for(None)

    def show_history_for_window(self, window_id: UsageWindowId) -> None:
        self._show_history_for(window_id)

    def _show_history_for(self, window_id: UsageWindowId | None) -> None:
        dialog = self._history_dialog
        if dialog is None:
            dialog = HistoryDialog(self._history_controller)
            self._history_dialog = dialog
        dialog.open_history(window_id=window_id)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _close(self) -> None:
        dialog = self._history_dialog
        if dialog is not None:
            dialog.hide()
        self._history_controller.close()
        super()._close()


def run_tray(
    provider: UsageProvider,
    settings: AppSettings,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController,
) -> int:
    instance = QApplication.instance()
    app = instance if isinstance(instance, QApplication) else QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    shell = HistoricalTrayShell(
        app,
        provider,
        settings,
        repository,
        notifier,
        history_controller,
    )
    shell.start()
    return app.exec()
