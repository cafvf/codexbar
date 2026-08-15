from __future__ import annotations

import sys
import traceback
from datetime import datetime
from typing import cast

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from codexbar.application.alerts import AlertService
from codexbar.application.plan_alerts import PlanAlertService
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.settings import SettingsRepository
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.settings import AppSettings
from codexbar.ui.controller import (
    DEFAULT_TRAY_SETTINGS,
    TrayController,
    TrayPhase,
    TrayViewState,
    apply_refresh_interval,
)
from codexbar.ui.errors import SystemTrayUnavailableError
from codexbar.ui.native_indicator import NativeIndicator, create_ayatana_indicator
from codexbar.ui.settings import SettingsActions, SettingsDialog


class UsagePanel(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CodexBar")
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setMinimumWidth(320)

        self._layout = QVBoxLayout(self)
        self._status = QLabel("Loading Codex usage…")
        self._layout.addWidget(self._status)
        self._windows = QVBoxLayout()
        self._layout.addLayout(self._windows)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.quit_button = QPushButton("Quit")
        controls.addStretch(1)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.quit_button)
        self._layout.addLayout(controls)

    def render_state(self, state: TrayViewState) -> None:
        self._clear_windows()
        usage = state.usage

        if state.phase is TrayPhase.LOADING:
            self._status.setText("Refreshing…")
        elif state.phase is TrayPhase.ERROR:
            self._status.setText(f"Error: {state.message or 'unknown error'}")
        elif state.phase is TrayPhase.STALE:
            self._status.setText("Showing cached data — refresh failed")
        else:
            self._status.setText("Up to date")

        if usage is None:
            return

        if not usage.windows:
            self._windows.addWidget(QLabel("No usage windows reported by Codex."))
        for window in usage.windows:
            self._add_window(window.label, window.percent_left, window.reset_at)

        observed = usage.observed_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        self._windows.addWidget(QLabel(f"Observed: {observed}"))

    def _add_window(self, label: str, percent_left: int, reset_at: datetime | None) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.addWidget(QLabel(f"{label}: {percent_left}% left"))

        progress = QProgressBar(container)
        progress.setRange(0, 100)
        progress.setValue(percent_left)
        progress.setTextVisible(False)
        layout.addWidget(progress)

        if reset_at is not None:
            reset_text = reset_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")
            layout.addWidget(QLabel(f"Reset: {reset_text}"))
        self._windows.addWidget(container)

    def _clear_windows(self) -> None:
        while self._windows.count():
            item = self._windows.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


def create_codexbar_icon(size: int = 64) -> QIcon:
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    background = QColor("#202123")
    foreground = QColor("#f2f2f2")
    painter.setBrush(background)
    painter.setPen(Qt.PenStyle.NoPen)
    margin = size * 0.08
    painter.drawRoundedRect(
        QRectF(margin, margin, size - 2 * margin, size - 2 * margin),
        size * 0.2,
        size * 0.2,
    )

    pen = QPen(foreground)
    pen.setWidthF(max(2.0, size * 0.065))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    painter.drawLine(
        QPoint(int(size * 0.29), int(size * 0.34)),
        QPoint(int(size * 0.47), int(size * 0.50)),
    )
    painter.drawLine(
        QPoint(int(size * 0.47), int(size * 0.50)),
        QPoint(int(size * 0.29), int(size * 0.66)),
    )
    painter.drawLine(
        QPoint(int(size * 0.51), int(size * 0.67)),
        QPoint(int(size * 0.72), int(size * 0.67)),
    )
    painter.end()
    return QIcon(pixmap)


def codexbar_icon_png(size: int = 64) -> bytes:
    pixmap = create_codexbar_icon(size).pixmap(size, size)
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError("unable to allocate icon buffer")
    if not pixmap.save(buffer, "PNG"):
        raise RuntimeError("unable to serialize CodexBar icon")
    return cast(bytes, data.data())


class TrayShell:
    def __init__(
        self,
        app: QApplication,
        provider: UsageProvider,
        settings: AppSettings,
        repository: SettingsRepository,
        notifier: NotificationPort,
        *,
        panel: UsagePanel | None = None,
    ) -> None:
        self._app = app
        self._settings = settings
        self._controller = TrayController(
            RefreshCoordinator(GetCurrentUsage(provider)),
            usage_policy=settings.usage_policy(),
            alert_service=AlertService(notifier),
            notifications_enabled=settings.notifications_enabled,
            plan_alert_service=PlanAlertService(notifier, settings),
        )
        self._settings_actions = SettingsActions(repository, self.apply_settings)
        self._settings_dialog: SettingsDialog | None = None
        self._last_rendered_state: TrayViewState | None = None

        self._panel = panel or UsagePanel()
        self._panel.refresh_button.clicked.connect(self.refresh)
        self._panel.quit_button.clicked.connect(app.quit)

        self._native_indicator: NativeIndicator | None = create_ayatana_indicator(
            icon_png=codexbar_icon_png(),
            on_refresh=self.refresh,
            on_details=self.show_panel,
            on_quit=app.quit,
            on_settings=self.show_settings,
        )

        self._tray: QSystemTrayIcon | None = None
        if self._native_indicator is None:
            self._ensure_qt_tray()

        self._menu = QMenu()
        self._summary_action = QAction("Loading usage…", self._menu)
        self._summary_action.setEnabled(False)
        refresh_action = QAction("Refresh", self._menu)
        refresh_action.triggered.connect(self.refresh)
        details_action = QAction("Open details", self._menu)
        details_action.triggered.connect(self.show_panel)
        settings_action = QAction("Settings", self._menu)
        settings_action.triggered.connect(self.show_settings)
        quit_action = QAction("Quit", self._menu)
        quit_action.triggered.connect(app.quit)
        self._menu.addAction(self._summary_action)
        self._menu.addSeparator()
        self._menu.addAction(refresh_action)
        self._menu.addAction(details_action)
        self._menu.addAction(settings_action)
        self._menu.addSeparator()
        self._menu.addAction(quit_action)
        if self._tray is not None:
            self._tray.setContextMenu(self._menu)

        self._refresh_timer = QTimer(app)
        apply_refresh_interval(self._refresh_timer, settings)
        self._refresh_timer.timeout.connect(self.refresh)

        self._poll_timer = QTimer(app)
        self._poll_timer.setInterval(DEFAULT_TRAY_SETTINGS.poll_interval_milliseconds)
        self._poll_timer.timeout.connect(self._poll)

        self._native_event_timer = QTimer(app)
        self._native_event_timer.setInterval(20)
        if self._native_indicator is not None:
            self._native_event_timer.timeout.connect(self._native_indicator.pump_events)

        app.aboutToQuit.connect(self._close)

    def apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        self._controller.apply_usage_policy(settings.usage_policy())
        self._controller.apply_notifications_enabled(settings.notifications_enabled)
        self._controller.apply_plan_settings(settings)
        apply_refresh_interval(self._refresh_timer, settings)

    def show_settings(self) -> None:
        dialog = self._settings_dialog
        if dialog is not None:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            return

        dialog = SettingsDialog(self._settings, self._settings_actions, self._panel)
        self._settings_dialog = dialog
        dialog.finished.connect(self._settings_dialog_finished)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _settings_dialog_finished(self, _result: int) -> None:
        self._settings_dialog = None

    def start(self) -> None:
        if self._native_indicator is not None:
            self._native_indicator.show()
            self._native_event_timer.start()
        elif self._tray is not None:
            self._tray.show()
        self._poll_timer.start()
        self._refresh_timer.start()
        self.refresh()

    def refresh(self) -> None:
        if self._controller.start_refresh():
            self._apply_state(self._controller.state)

    def _poll(self) -> None:
        previous = self._controller.state
        try:
            state = self._controller.poll()
        except Exception as exc:  # keep unexpected worker failures inside the GUI boundary
            traceback.print_exc()
            self._apply_state(
                TrayViewState(
                    phase=TrayPhase.ERROR,
                    usage=previous.usage,
                    message=f"Unexpected refresh failure: {exc}",
                )
            )
            return

        self._supervise_native_indicator()
        if state != previous:
            self._apply_state(state)
            self._on_controller_transition(previous, state)

    def _apply_state(self, state: TrayViewState) -> None:
        if state == self._last_rendered_state:
            return
        self._last_rendered_state = state
        self._panel.render_state(state)
        self._summary_action.setText(self._menu_summary(state))

        if self._native_indicator is not None:
            self._native_indicator.set_glance(
                state.usage.glance_text if state.usage is not None else state.phase.value,
                stale=state.phase is TrayPhase.STALE,
            )
        elif self._tray is not None:
            self._tray.setToolTip(self._tooltip(state))

    def _on_controller_transition(
        self,
        _previous: TrayViewState,
        _current: TrayViewState,
    ) -> None:
        """Lifecycle hook for composed shells; current TrayController remains history-free."""

    def _supervise_native_indicator(self) -> None:
        indicator = self._native_indicator
        if indicator is None or indicator.is_healthy():
            return
        indicator.close()
        self._native_indicator = None
        self._native_event_timer.stop()
        self._activate_qt_fallback()

    def _ensure_qt_tray(self) -> None:
        if self._tray is not None:
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise SystemTrayUnavailableError("system tray is not available in this desktop session")
        self._tray = QSystemTrayIcon(create_codexbar_icon(), self._app)
        self._tray.setToolTip("CodexBar")
        self._tray.activated.connect(self._on_tray_activated)

    def _activate_qt_fallback(self) -> None:
        self._ensure_qt_tray()
        if self._tray is not None:
            self._tray.setContextMenu(self._menu)
            self._tray.show()

    def _tooltip(self, state: TrayViewState) -> str:
        if state.usage is None:
            return f"CodexBar — {state.phase.value}"
        summary = state.usage.glance_text or "no windows"
        suffix = " [stale]" if state.phase is TrayPhase.STALE else ""
        return f"CodexBar — {summary}{suffix}"

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.toggle_panel()

    def toggle_panel(self) -> None:
        if self._panel.isVisible():
            self._panel.hide()
        else:
            self.show_panel()

    def _menu_summary(self, state: TrayViewState) -> str:
        if state.usage is None:
            return f"CodexBar — {state.phase.value}"
        summary = state.usage.glance_text or "no windows"
        if state.phase is TrayPhase.STALE:
            return f"{summary} · stale"
        if state.phase is TrayPhase.ERROR:
            return f"{summary} · error"
        return summary

    def _close(self) -> None:
        self._poll_timer.stop()
        self._refresh_timer.stop()
        self._native_event_timer.stop()
        self._controller.close()
        if self._native_indicator is not None:
            self._native_indicator.close()

    def show_panel(self) -> None:
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()


def run_tray(
    provider: UsageProvider,
    settings: AppSettings,
    repository: SettingsRepository,
    notifier: NotificationPort,
) -> int:
    instance = QApplication.instance()
    app = instance if isinstance(instance, QApplication) else QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    shell = TrayShell(app, provider, settings, repository, notifier)
    shell.start()
    return app.exec()
