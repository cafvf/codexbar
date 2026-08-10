from __future__ import annotations

import traceback
from datetime import datetime
from decimal import Decimal

from PySide6.QtCore import QPointF, QRectF, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import (
    QCloseEvent,
    QHideEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPalette,
    QPen,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codexbar.application.analytics import AnalysisPeriod
from codexbar.domain.models import UsageWindowId
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_viewmodel import (
    HistoryChartPoint,
    HistorySummaryViewState,
    HistoryViewPhase,
    HistoryViewState,
)

_PERIOD_LABELS = {
    AnalysisPeriod.HOURS_24: "24h",
    AnalysisPeriod.DAYS_7: "7d",
    AnalysisPeriod.DAYS_30: "30d",
}


class HistoryChart(QWidget):
    """Small dependency-free renderer for discrete observed history points."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._points: tuple[HistoryChartPoint, ...] = ()
        self._interval_start: datetime | None = None
        self._interval_end: datetime | None = None
        self._period = AnalysisPeriod.HOURS_24
        self.setMinimumSize(560, 250)

    @property
    def points(self) -> tuple[HistoryChartPoint, ...]:
        return self._points

    def set_domain(
        self,
        start: datetime | None,
        end: datetime | None,
        period: AnalysisPeriod,
    ) -> None:
        self._interval_start = start
        self._interval_end = end
        self._period = period
        self.update()

    def set_points(self, points: tuple[HistoryChartPoint, ...]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        bounds = QRectF(self.rect()).adjusted(58.0, 16.0, -18.0, -54.0)
        self._draw_axes(painter, bounds)
        if not self._points:
            painter.drawText(
                bounds,
                Qt.AlignmentFlag.AlignCenter,
                "No observations in the selected period.",
            )
            return

        coordinates = self._coordinates(bounds)
        if len(coordinates) > 1:
            path = QPainterPath(coordinates[0])
            for coordinate in coordinates[1:]:
                path.lineTo(coordinate)
            line_color = self.palette().color(QPalette.ColorRole.Highlight)
            painter.setPen(QPen(line_color, 2.0))
            painter.drawPath(path)

        point_color = self.palette().color(QPalette.ColorRole.Highlight)
        painter.setPen(QPen(point_color, 1.5))
        painter.setBrush(point_color)
        for coordinate in coordinates:
            painter.drawEllipse(coordinate, 3.5, 3.5)

    def _draw_axes(self, painter: QPainter, bounds: QRectF) -> None:
        axis_color = self.palette().color(QPalette.ColorRole.Text)
        grid_color = self.palette().color(QPalette.ColorRole.Mid)
        painter.setPen(QPen(axis_color, 1.0))
        painter.drawLine(bounds.bottomLeft(), bounds.bottomRight())
        painter.drawLine(bounds.topLeft(), bounds.bottomLeft())

        for percent in (0, 25, 50, 75, 100):
            fraction = percent / 100
            y = bounds.bottom() - fraction * bounds.height()
            painter.setPen(QPen(grid_color, 0.7))
            painter.drawLine(
                QPointF(bounds.left(), y),
                QPointF(bounds.right(), y),
            )
            painter.setPen(QPen(axis_color, 1.0))
            painter.drawText(
                QRectF(0.0, y - 10.0, 42.0, 20.0),
                Qt.AlignmentFlag.AlignRight,
                f"{percent}%",
            )

        if self._interval_start is not None and self._interval_end is not None:
            for tick_time, label in _time_ticks(
                self._interval_start,
                self._interval_end,
                self._period,
            ):
                fraction = _time_fraction(
                    tick_time,
                    self._interval_start,
                    self._interval_end,
                )
                x = bounds.left() + fraction * bounds.width()
                painter.setPen(QPen(grid_color, 0.7))
                painter.drawLine(
                    QPointF(x, bounds.top()),
                    QPointF(x, bounds.bottom()),
                )
                painter.setPen(QPen(axis_color, 1.0))
                painter.drawText(
                    QRectF(x - 45.0, bounds.bottom() + 7.0, 90.0, 34.0),
                    Qt.AlignmentFlag.AlignHCenter
                    | Qt.AlignmentFlag.AlignTop,
                    label,
                )

    def _coordinates(self, bounds: QRectF) -> tuple[QPointF, ...]:
        if self._interval_start is None or self._interval_end is None:
            start = self._points[0].observed_at
            end = self._points[-1].observed_at
        else:
            start = self._interval_start
            end = self._interval_end

        result: list[QPointF] = []
        for point in self._points:
            x_fraction = _time_fraction(point.observed_at, start, end)
            x = bounds.left() + x_fraction * bounds.width()
            y_fraction = float(point.percent_left / Decimal("100"))
            y = bounds.bottom() - y_fraction * bounds.height()
            result.append(QPointF(x, y))
        return tuple(result)


class HistoryDialog(QDialog):
    def __init__(
        self,
        controller: HistoryController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._last_state: HistoryViewState | None = None
        self._focused_window_id: UsageWindowId | None = None
        self.setWindowTitle("CodexBar — Usage history")
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox(self)
        for period, label in _PERIOD_LABELS.items():
            self.period_combo.addItem(label, period.value)
        controls.addWidget(self.period_combo)

        self.refresh_button = QPushButton("Reload history", self)
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)

        self.status_label = QLabel("Loading history…", self)
        layout.addWidget(self.status_label)

        self.summary_widget = QWidget(self)
        summary_layout = QGridLayout(self.summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        self._summary_values: dict[str, QLabel] = {}
        for row, (key, title) in enumerate(
            (
                ("count", "Observations"),
                ("first", "First observation"),
                ("latest", "Latest observation"),
                ("first_remaining", "First remaining"),
                ("latest_remaining", "Latest remaining"),
                ("minimum", "Observed minimum"),
                ("maximum", "Observed maximum"),
                ("change", "Observed change"),
            )
        ):
            summary_layout.addWidget(QLabel(f"{title}:"), row, 0)
            value = QLabel("—", self.summary_widget)
            summary_layout.addWidget(value, row, 1)
            self._summary_values[key] = value
        layout.addWidget(self.summary_widget)

        self.chart = HistoryChart(self)
        layout.addWidget(self.chart)

        note = QLabel(
            "Points are stored observations. Connecting segments are a visual aid, "
            "not reconstructed usage between observations.",
            self,
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        self.period_combo.currentIndexChanged.connect(self._period_changed)
        self.refresh_button.clicked.connect(self.refresh)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll)

    def open_history(
        self,
        *,
        window_id: UsageWindowId | None = None,
    ) -> None:
        period = self._selected_period()
        self._focused_window_id = window_id
        self._controller.start(period, window_id=window_id)
        self.render_state(self._controller.state)

    def refresh(self) -> None:
        self._controller.start(
            self._selected_period(),
            window_id=self._focused_window_id,
        )
        self.render_state(self._controller.state)

    def render_state(self, state: HistoryViewState) -> None:
        self._last_state = state
        self._sync_period(state.period)
        if state.selected_window_id is not None:
            self._focused_window_id = state.selected_window_id
        self._render_status(state)
        self.refresh_button.setEnabled(state.phase is not HistoryViewPhase.LOADING)
        self.chart.set_domain(
            state.interval_start,
            state.interval_end,
            state.period,
        )
        self.chart.set_points(state.chart_points)
        self._render_summary(state.summary)

    def _poll(self) -> None:
        try:
            state = self._controller.poll()
        except Exception as exc:
            traceback.print_exc()
            self.status_label.setText(f"Usage history internal error: {exc}")
            self.refresh_button.setEnabled(True)
            return
        if state != self._last_state:
            self.render_state(state)

    def _period_changed(self, _index: int) -> None:
        if self._last_state is None:
            return
        self._controller.start(
            self._selected_period(),
            window_id=self._focused_window_id,
        )
        self._set_loading_status()

    def _set_loading_status(self) -> None:
        self.status_label.setText("Loading historical usage…")
        self.refresh_button.setEnabled(False)

    def _selected_period(self) -> AnalysisPeriod:
        value = self.period_combo.currentData()
        try:
            return AnalysisPeriod(str(value))
        except ValueError:
            return AnalysisPeriod.HOURS_24

    def _sync_period(self, period: AnalysisPeriod) -> None:
        with QSignalBlocker(self.period_combo):
            index = self.period_combo.findData(period.value)
            if index >= 0:
                self.period_combo.setCurrentIndex(index)

    def _render_status(self, state: HistoryViewState) -> None:
        if state.phase is HistoryViewPhase.LOADING:
            text = "Loading history…"
        elif state.phase is HistoryViewPhase.READY:
            selected = state.selected_label or "selected window"
            identity = (
                state.selected_window_id.value
                if state.selected_window_id is not None
                else "unknown"
            )
            text = f"Observed history — {selected} [{identity}]"
        elif state.phase is HistoryViewPhase.EMPTY:
            text = "No stored observations in the selected period."
        elif state.phase is HistoryViewPhase.UNSUPPORTED:
            text = "Stored history uses an unsupported schema."
        else:
            text = "Usage history is unavailable."
        if state.diagnostic and state.phase in {
            HistoryViewPhase.UNAVAILABLE,
            HistoryViewPhase.UNSUPPORTED,
        }:
            text = f"{text} {state.diagnostic}"
        self.status_label.setText(text)

    def _render_summary(self, summary: HistorySummaryViewState | None) -> None:
        if summary is None:
            for label in self._summary_values.values():
                label.setText("—")
            return
        self._summary_values["count"].setText(str(summary.observation_count))
        self._summary_values["first"].setText(_format_datetime(summary.first_observed_at))
        self._summary_values["latest"].setText(_format_datetime(summary.latest_observed_at))
        self._summary_values["first_remaining"].setText(
            _format_percent(summary.first_percent_left)
        )
        self._summary_values["latest_remaining"].setText(
            _format_percent(summary.latest_percent_left)
        )
        self._summary_values["minimum"].setText(
            _format_percent(summary.observed_min_percent_left)
        )
        self._summary_values["maximum"].setText(
            _format_percent(summary.observed_max_percent_left)
        )
        change = summary.observed_change_percentage_points
        self._summary_values["change"].setText(
            "—" if change is None else f"{_format_decimal(change)} pp"
        )

    def showEvent(self, event: QShowEvent) -> None:
        self._poll_timer.start()
        super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self._poll_timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        event.ignore()



def _time_fraction(
    value: datetime,
    start: datetime,
    end: datetime,
) -> float:
    span = (end - start).total_seconds()
    if span <= 0:
        return 0.0
    fraction = (value - start).total_seconds() / span
    return min(1.0, max(0.0, fraction))


def _time_ticks(
    start: datetime,
    end: datetime,
    period: AnalysisPeriod,
) -> tuple[tuple[datetime, str], ...]:
    span = end - start
    ticks = tuple(start + span * (index / 4) for index in range(5))
    return tuple(
        (tick, _format_time_tick(tick, period, is_end=index == 4))
        for index, tick in enumerate(ticks)
    )


def _format_time_tick(
    value: datetime,
    period: AnalysisPeriod,
    *,
    is_end: bool,
) -> str:
    local = value.astimezone()
    if is_end:
        return f"now\n{local:%m-%d %H:%M}"
    if period is AnalysisPeriod.HOURS_24:
        return local.strftime("%m-%d\n%H:%M")
    return local.strftime("%m-%d")

def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _format_percent(value: Decimal) -> str:
    return f"{_format_decimal(value)}%"


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")
