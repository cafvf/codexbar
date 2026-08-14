from __future__ import annotations

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from codexbar.application.instance_ownership import InstanceOwnerBinding
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager, RedeemResult
from codexbar.application.redeem_execution import RedeemExecutionController
from codexbar.application.runtime_health import RuntimeDiagnosticRegistry
from codexbar.application.settings import SettingsRepository
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    EvidenceOrigin,
    OperationalHealth,
    SubsystemHealth,
    SubsystemRole,
)
from codexbar.domain.models import UsageWindowId
from codexbar.domain.settings import AppSettings
from codexbar.ui.context_controller import ContextController
from codexbar.ui.context_history_dialog import ContextHistoryDialog
from codexbar.ui.context_viewmodel import ContextPresenter
from codexbar.ui.control_panel import CurrentAccountPanel
from codexbar.ui.controller import TrayViewState
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_tray import HistoricalTrayShell
from codexbar.ui.native_indicator import AyatanaHelperIndicator
from codexbar.ui.system_health_panel import SystemHealthDialog
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter


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
        *,
        context_controller: ContextController | None = None,
        redeem_controller: RedeemExecutionController | None = None,
        health_presenter: SystemHealthPresenter | None = None,
        runtime_diagnostics: RuntimeDiagnosticRegistry | None = None,
    ) -> None:
        self._presenter = presenter
        context_controller = context_controller or presenter.runtime_context_controller
        self._context_controller = context_controller
        redeem_controller = redeem_controller or presenter.runtime_redeem_controller
        health_presenter = health_presenter or presenter.runtime_health_presenter
        runtime_diagnostics = runtime_diagnostics or presenter.runtime_diagnostics
        self._runtime_diagnostics = runtime_diagnostics
        self._health_presenter = health_presenter
        self._health_dialog: SystemHealthDialog | None = None
        panel = CurrentAccountPanel(
            presenter,
            redeem_manager,
            redeem_controller=redeem_controller,
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
        self._install_system_health_actions()
        self._sync_backend_diagnostics()

    def _install_system_health_actions(self) -> None:
        if self._health_presenter is None:
            return
        action = QAction("System health", self._menu)
        action.triggered.connect(self.show_system_health)
        settings_action = next(
            (item for item in self._menu.actions() if item.text() == "Settings"),
            None,
        )
        if settings_action is None:
            self._menu.addAction(action)
        else:
            self._menu.insertAction(settings_action, action)
        native = self._native_indicator
        if isinstance(native, AyatanaHelperIndicator):
            native._callbacks["health"] = self.show_system_health

    def show_system_health(self) -> None:
        presenter = self._health_presenter
        if presenter is None:
            return
        dialog = self._health_dialog
        if dialog is None:
            dialog = SystemHealthDialog(presenter, self._control_panel)
            self._health_dialog = dialog
            dialog.finished.connect(self._system_health_finished)
        dialog.refresh()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _system_health_finished(self, _result: int) -> None:
        self._health_dialog = None

    def _show_history_for(self, window_id: UsageWindowId | None) -> None:
        context_controller = self._context_controller
        if context_controller is None:
            super()._show_history_for(window_id)
            return

        dialog = self._history_dialog
        if not isinstance(dialog, ContextHistoryDialog):
            dialog = ContextHistoryDialog(
                self._history_controller,
                context_controller,
            )
            self._history_dialog = dialog
        dialog.open_history(window_id=window_id)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _apply_state(self, state: TrayViewState) -> None:
        previous = self._last_rendered_state
        try:
            super()._apply_state(state)
        except Exception:
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

    def _close(self) -> None:
        dialog = self._health_dialog
        if dialog is not None:
            dialog.hide()
        super()._close()

    def _supervise_native_indicator(self) -> None:
        indicator = self._native_indicator
        if indicator is None or indicator.is_healthy():
            return
        recent_stderr = (
            indicator.recent_stderr
            if isinstance(indicator, AyatanaHelperIndicator)
            else ""
        )
        super()._supervise_native_indicator()
        self._sync_backend_diagnostics(native_failure_stderr=recent_stderr)

    def _sync_backend_diagnostics(
        self,
        *,
        native_failure_stderr: str | None = None,
    ) -> None:
        registry = self._runtime_diagnostics
        if registry is None:
            return

        native = self._native_indicator
        if native is not None:
            recent = (
                native.recent_stderr
                if isinstance(native, AyatanaHelperIndicator)
                else ""
            )
            details = (
                (DiagnosticDetail("stderr_line_count", len(recent.splitlines())),)
                if recent
                else ()
            )
            registry.upsert(
                SubsystemHealth(
                    name="native_indicator",
                    role=SubsystemRole.NATIVE_INDICATOR,
                    availability=DiagnosticAvailability.AVAILABLE,
                    operational_health=OperationalHealth.OK,
                    evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                    summary="Ayatana native indicator helper is active.",
                    details=details,
                )
            )
            registry.upsert(
                SubsystemHealth(
                    name="qt_fallback",
                    role=SubsystemRole.QT_FALLBACK,
                    availability=DiagnosticAvailability.NOT_APPLICABLE,
                    operational_health=OperationalHealth.OK,
                    evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                    summary="Qt tray fallback is on standby while native indicator is healthy.",
                )
            )
            return

        details = (
            (
                DiagnosticDetail(
                    "stderr_line_count",
                    len(native_failure_stderr.splitlines()),
                ),
            )
            if native_failure_stderr
            else ()
        )
        registry.upsert(
            SubsystemHealth(
                name="native_indicator",
                role=SubsystemRole.NATIVE_INDICATOR,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=(
                    OperationalHealth.DEGRADED
                    if native_failure_stderr
                    else OperationalHealth.OK
                ),
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                summary=(
                    "Native indicator failed; Qt fallback is active."
                    if native_failure_stderr
                    else "Native indicator is unavailable; Qt fallback is active."
                ),
                details=details,
            )
        )
        registry.upsert(
            SubsystemHealth(
                name="qt_fallback",
                role=SubsystemRole.QT_FALLBACK,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                summary="Qt system-tray fallback is active.",
            )
        )


def run_tray(
    provider: UsageProvider,
    settings: AppSettings,
    repository: SettingsRepository,
    notifier: NotificationPort,
    history_controller: HistoryController,
    presenter: CurrentAccountPresenter,
    redeem_manager: RedeemProcessManager | None,
    context_presenter: ContextPresenter | None = None,
    instance_owner: InstanceOwnerBinding | None = None,
    context_controller: ContextController | None = None,
    redeem_controller: RedeemExecutionController | None = None,
    health_presenter: SystemHealthPresenter | None = None,
    runtime_diagnostics: RuntimeDiagnosticRegistry | None = None,
) -> int:
    instance = QApplication.instance()
    app = instance if isinstance(instance, QApplication) else QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    runtime_diagnostics = runtime_diagnostics or presenter.runtime_diagnostics
    if instance_owner is not None and runtime_diagnostics is not None:
        runtime_diagnostics.upsert(instance_owner.diagnostic.as_subsystem_health())
    context_controller = context_controller or presenter.runtime_context_controller
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
        context_controller=context_controller,
        redeem_controller=redeem_controller,
        health_presenter=health_presenter,
        runtime_diagnostics=runtime_diagnostics,
    )
    if instance_owner is not None:
        instance_owner.bind_show_details(shell.show_panel)
    shell.start()
    return app.exec()
