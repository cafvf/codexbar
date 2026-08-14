from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from codexbar.ui.system_health_viewmodel import (
    SystemHealthPresenter,
    SystemHealthSubsystemViewState,
    SystemHealthViewState,
)


class SystemHealthPanel(QFrame):
    """Read-only health summary with optional technical diagnostics."""

    def __init__(
        self,
        presenter: SystemHealthPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("System health", self)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        intro = QLabel(
            "A read-only summary of the CodexBar runtime. Green/healthy items need no "
            "action. Technical counters and timing data are hidden by default.",
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._summary = QLabel("System health is initializing.", self)
        self._summary.setWordWrap(True)
        self._summary.setTextFormat(Qt.TextFormat.RichText)
        self._summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._summary)

        self._technical_toggle = QCheckBox("Show technical details", self)
        self._technical_toggle.toggled.connect(self._technical_visibility_changed)
        layout.addWidget(self._technical_toggle)

        self._technical = QLabel("", self)
        self._technical.setWordWrap(True)
        self._technical.setTextFormat(Qt.TextFormat.RichText)
        self._technical.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._technical.setVisible(False)
        layout.addWidget(self._technical)
        layout.addStretch(1)

    def refresh(self) -> None:
        self.render_state(self._presenter.current())

    def render_state(self, state: SystemHealthViewState) -> None:
        self._summary.setText(_summary_html(state))
        self._technical.setText(_technical_html(state))

    def _technical_visibility_changed(self, checked: bool) -> None:
        self._technical.setVisible(checked)


class SystemHealthDialog(QDialog):
    """Independent, resizable System Health window opened from the tray menu."""

    def __init__(
        self,
        presenter: SystemHealthPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("CodexBar — System health")
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.resize(720, 560)
        self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.panel = SystemHealthPanel(presenter, scroll)
        scroll.setWidget(self.panel)
        layout.addWidget(scroll)

        controls = QHBoxLayout()
        auto_refresh = QLabel(
            "Updates automatically while this window is open.",
            self,
        )
        controls.addWidget(auto_refresh)
        controls.addStretch(1)
        close = QPushButton("Close", self)
        close.clicked.connect(self.close)
        controls.addWidget(close)
        layout.addLayout(controls)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(750)
        self._refresh_timer.timeout.connect(self.refresh)

    def refresh(self) -> None:
        self.panel.refresh()

    def showEvent(self, event: QShowEvent) -> None:
        self.refresh()
        self._refresh_timer.start()
        super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self._refresh_timer.stop()
        super().hideEvent(event)


def _summary_html(state: SystemHealthViewState) -> str:
    parts = [
        '<div style="margin-bottom: 12px;">',
        f"<b>Overall status: {escape(state.overall_label)}</b><br>",
        escape(state.overall_summary),
        "</div>",
    ]

    notes = tuple(
        item
        for item in state.subsystems
        if item.name in {"history_lineage", "reset_monitor"}
    )
    components = tuple(
        item
        for item in state.subsystems
        if item.name not in {"history_lineage", "reset_monitor"}
    )

    if notes:
        parts.append("<h3>Important notes</h3>")
        parts.extend(_note_html(item) for item in notes)

    if components:
        parts.append("<h3>Components</h3>")
        parts.extend(_subsystem_html(item) for item in components)

    return "".join(parts)


def _subsystem_html(item: SystemHealthSubsystemViewState) -> str:
    return (
        '<div style="margin-bottom: 10px;">'
        f"<b>{escape(item.title)} — {escape(item.status_label)}</b><br>"
        f"{escape(item.display_summary)}"
        "</div>"
    )


def _note_html(item: SystemHealthSubsystemViewState) -> str:
    return (
        '<div style="margin-bottom: 10px;">'
        f"<b>{escape(item.title)}</b><br>"
        f"{escape(item.display_summary)}"
        "</div>"
    )


def _technical_html(state: SystemHealthViewState) -> str:
    parts = [
        "<h3>Technical details</h3>",
        "<p>These values are intended for troubleshooting and release evidence.</p>",
        "<h4>How to read these details</h4>",
        "<p><b>Revision</b> — an internal version counter. It increases when "
        "read-visible Current or History data changes. Matching revisions help "
        "CodexBar know whether a cached Historical Context result is still valid.</p>",
        "<p><b>p95</b> — the 95th-percentile duration. In practical terms, 95% "
        "of the retained measurements completed in this time or faster. It is "
        "used here to spot unusually slow runtime operations.</p>",
        "<p><b>p50 / median</b> — the middle retained measurement: half of the "
        "samples were faster and half were slower.</p>",
        f"<p><b>Snapshot generated:</b> {escape(state.generated_at)}</p>",
        "<h4>Runtime measurements</h4>",
    ]

    if state.runtime_metrics:
        parts.append("<ul>")
        parts.extend(
            f"<li>{escape(metric.summary)}</li>" for metric in state.runtime_metrics
        )
        parts.append("</ul>")
    else:
        parts.append(
            "<p>No runtime measurement samples have been retained yet. "
            "Use Refresh, open Usage history, or perform a manual redeem and "
            "reopen this section to populate the measurements.</p>"
        )

    parts.append("<h4>Component evidence</h4>")
    for item in state.subsystems:
        parts.append(
            '<div style="margin-bottom: 10px;">'
            f"<b>{escape(item.title)}</b> "
            f"<code>({escape(item.name)})</code><br>"
            f"Role: {escape(item.role)} · Availability: {escape(item.availability)} · "
            f"Health: {escape(item.operational_health)} · "
            f"Freshness: {escape(item.freshness)}"
        )
        if item.technical_details:
            parts.append("<ul>")
            parts.extend(
                f"<li>{escape(detail)}</li>" for detail in item.technical_details
            )
            parts.append("</ul>")
        parts.append("</div>")

    return "".join(parts)
