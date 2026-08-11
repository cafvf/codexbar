from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager, RedeemResult
from codexbar.application.settings import SettingsRepository
from codexbar.domain.settings import AppSettings
from codexbar.ui.context_viewmodel import ContextPresenter
from codexbar.ui.control_panel import CurrentAccountPanel
from codexbar.ui.controller import TrayViewState
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
        context_presenter: ContextPresenter | None = None,
    ) -> None:
        self._presenter = presenter
        panel = CurrentAccountPanel(
            presenter,
            redeem_manager,
            context_presenter=context_presenter,
            on_history=self.show_history_for_window,
            on_redeem_changed=self._on_redeem_changed,
        )
        self._control_panel = panel
        super().__init__(
            app,
            provider,
            settings,
            repository,
            notifier,
            history_controller,
            panel=panel,
        )

    def _apply_state(self, state: TrayViewState) -> None:
        previous = self._last_rendered_state
        try:
            super()._apply_state(state)
        except Exception:
            # Parent marks before rendering; restore so a failed optional render can retry.
            self._last_rendered_state = previous
            raise

    def apply_settings(self, settings: AppSettings) -> None:
        super().apply_settings(settings)
        self._presenter.apply_settings(settings)

    def _on_redeem_changed(self, result: RedeemResult) -> None:
        observation = result.observation
        if observation is None:
            if result.refetch_error is not None:
                self.refresh()
            else:
                self._control_panel.render_state(self._controller.state)
            return

        previous = self._controller.state
        state = self._controller.adopt_snapshot(observation.usage)
        self._apply_state(state)
        self._on_controller_transition(previous, state)


def run_tray(
    provider: UsageProvider,
    settings: AppSettings,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController,
    presenter: CurrentAccountPresenter,
    redeem_manager: RedeemProcessManager | None,
    context_presenter: ContextPresenter | None = None,
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
        context_presenter,
    )
    shell.start()
    return app.exec()
