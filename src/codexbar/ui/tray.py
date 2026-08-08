from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import QPoint, QRectF, QSize, QTimer, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap
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

from codexbar.application.ports import UsageProvider
from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.ui.controller import TrayController, TrayPhase, TraySettings, TrayViewState
from codexbar.ui.errors import SystemTrayUnavailableError


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

    def render(self, state: TrayViewState) -> None:
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
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


def create_codexbar_icon(size: int = 64) -> QIcon:
    """Create a small project-owned terminal-style icon without third-party branding."""

    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    background = QColor("#202123")
    foreground = QColor("#f2f2f2")
    painter.setBrush(background)
    painter.setPen(Qt.PenStyle.NoPen)
    margin = size * 0.08
    painter.drawRoundedRect(QRectF(margin, margin, size - 2 * margin, size - 2 * margin), size * 0.2, size * 0.2)

    pen = QPen(foreground)
    pen.setWidthF(max(2.0, size * 0.065))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    painter.drawLine(QPoint(int(size * 0.29), int(size * 0.34)), QPoint(int(size * 0.47), int(size * 0.50)))
    painter.drawLine(QPoint(int(size * 0.47), int(size * 0.50)), QPoint(int(size * 0.29), int(size * 0.66)))
    painter.drawLine(QPoint(int(size * 0.51), int(size * 0.67)), QPoint(int(size * 0.72), int(size * 0.67)))
    painter.end()
    return QIcon(pixmap)


class TrayShell:
    def __init__(
        self,
        app: QApplication,
        provider: UsageProvider,
        settings: TraySettings,
    ) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise SystemTrayUnavailableError("system tray is not available in this desktop session")

        self._app = app
        self._settings = settings
        self._controller = TrayController(RefreshCoordinator(GetCurrentUsage(provider)))
        self._panel = UsagePanel()
        self._panel.refresh_button.clicked.connect(self.refresh)
        self._panel.quit_button.clicked.connect(app.quit)

        self._tray = QSystemTrayIcon(create_codexbar_icon(), app)
        self._tray.setToolTip("CodexBar")
        self._tray.activated.connect(self._on_tray_activated)

        # QSystemTrayIcon activation is desktop-dependent. In particular, GNOME-based
        # StatusNotifier/AppIndicator implementations may consume primary activation and
        # open the registered menu without emitting Trigger. Keep a registered menu as a
        # guaranteed control/quit surface, but make it useful immediately: the first
        # disabled action contains the live glance summary, so there is no Show indirection.
        self._menu = QMenu()
        self._summary_action = QAction("Loading usage…", self._menu)
        self._summary_action.setEnabled(False)
        refresh_action = QAction("Refresh", self._menu)
        refresh_action.triggered.connect(self.refresh)
        details_action = QAction("Open details", self._menu)
        details_action.triggered.connect(self.show_panel)
        quit_action = QAction("Quit", self._menu)
        quit_action.triggered.connect(app.quit)
        self._menu.addAction(self._summary_action)
        self._menu.addSeparator()
        self._menu.addAction(refresh_action)
        self._menu.addAction(details_action)
        self._menu.addSeparator()
        self._menu.addAction(quit_action)
        self._tray.setContextMenu(self._menu)

        self._refresh_timer = QTimer(app)
        self._refresh_timer.setInterval(settings.refresh_interval_seconds * 1000)
        self._refresh_timer.timeout.connect(self.refresh)

        self._poll_timer = QTimer(app)
        self._poll_timer.setInterval(settings.poll_interval_milliseconds)
        self._poll_timer.timeout.connect(self._poll)

        app.aboutToQuit.connect(self._controller.close)

    def start(self) -> None:
        self._tray.show()
        self._poll_timer.start()
        self._refresh_timer.start()
        self.refresh()

    def refresh(self) -> None:
        if self._controller.start_refresh():
            self._panel.render(self._controller.state)

    def _poll(self) -> None:
        state = self._controller.poll()
        self._panel.render(state)
        self._tray.setToolTip(self._tooltip(state))
        self._summary_action.setText(self._menu_summary(state))

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

    def show_panel(self) -> None:
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()


def run_tray(provider: UsageProvider, settings: TraySettings) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    shell = TrayShell(app, provider, settings)
    shell.start()
    return app.exec()
