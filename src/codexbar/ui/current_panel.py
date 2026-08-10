from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from codexbar.domain.models import UsageWindowId
from codexbar.ui.controller import TrayPhase, TrayViewState
from codexbar.ui.tray import UsagePanel
from codexbar.ui.viewmodel import UsageWindowViewState


class RichUsagePanel(UsagePanel):
    """Current-usage detail panel for v1.4."""

    def __init__(
        self,
        *,
        on_history: Callable[[UsageWindowId], None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__()
        self._on_history = on_history
        self._clock = clock or (lambda: datetime.now(UTC))
        self._observed_at: datetime | None = None
        self._observed_label: QLabel | None = None
        self.setMinimumWidth(380)

        self._age_timer = QTimer(self)
        self._age_timer.setInterval(1000)
        self._age_timer.timeout.connect(self._update_observation_age)
        self._age_timer.start()

    def render_state(self, state: TrayViewState) -> None:
        self._clear_windows()
        self._observed_at = None
        self._observed_label = None
        usage = state.usage
        now = self._now()

        if state.phase is TrayPhase.LOADING:
            self._status.setText("Refreshing current usage…")
        elif state.phase is TrayPhase.ERROR:
            self._status.setText(f"Current usage error: {state.message or 'unknown error'}")
        elif state.phase is TrayPhase.STALE:
            self._status.setText("Freshness: STALE — showing last valid current usage")
        else:
            self._status.setText("Freshness: CURRENT — up to date")

        if usage is None:
            return

        if not usage.windows:
            self._windows.addWidget(QLabel("No usage windows reported by Codex."))

        for window in usage.windows:
            self._add_current_window(window, now)

        self._observed_at = usage.observed_at
        self._observed_label = QLabel()
        self._windows.addWidget(self._observed_label)
        self._update_observation_age()

    def _add_current_window(
        self,
        window: UsageWindowViewState,
        now: datetime,
    ) -> None:
        container = QFrame(self)
        container.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        heading = QHBoxLayout()
        heading.addWidget(QLabel(window.label))
        heading.addStretch(1)
        heading.addWidget(QLabel(f"{window.percent_left}% left"))
        layout.addLayout(heading)

        layout.addWidget(QLabel(f"State: {window.state.value.upper()}"))

        progress = QProgressBar(container)
        progress.setRange(0, 100)
        progress.setValue(window.percent_left)
        progress.setFormat(f"{window.percent_left}%")
        progress.setTextVisible(True)
        layout.addWidget(progress)

        if window.reset_at is not None:
            absolute = _format_datetime(window.reset_at)
            relative = _format_reset_relative(now, window.reset_at)
            layout.addWidget(QLabel(f"Reset: {absolute} · {relative}"))
        else:
            layout.addWidget(QLabel("Reset: not reported"))

        if self._on_history is not None:
            history_button = QPushButton("View history", container)
            history_button.clicked.connect(
                lambda _checked=False, window_id=window.window_id: (
                    self._open_history(window_id)
                )
            )
            layout.addWidget(history_button)

        self._windows.addWidget(container)

    def _open_history(self, window_id: UsageWindowId) -> None:
        if self._on_history is not None:
            self._on_history(window_id)

    def _update_observation_age(self) -> None:
        observed_at = self._observed_at
        label = self._observed_label
        if observed_at is None or label is None:
            return
        now = self._now()
        absolute = _format_datetime(observed_at)
        age = _format_age(now, observed_at)
        label.setText(f"Observed: {absolute} · {age} ago")

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("current panel clock must be timezone-aware")
        return now.astimezone(UTC)


def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def _format_age(now: datetime, observed_at: datetime) -> str:
    delta = now - observed_at.astimezone(UTC)
    if delta.total_seconds() <= 0:
        return "0s"
    return _format_duration(delta)


def _format_reset_relative(now: datetime, reset_at: datetime) -> str:
    delta = reset_at.astimezone(UTC) - now
    if delta.total_seconds() <= 0:
        return "reset time passed"
    return f"in {_format_duration(delta)}"


def _format_duration(delta: timedelta) -> str:
    seconds = max(0, int(delta.total_seconds()))
    days, seconds = divmod(seconds, 86_400)
    hours, seconds = divmod(seconds, 3_600)
    minutes, seconds = divmod(seconds, 60)

    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"
