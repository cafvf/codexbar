from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from codexbar.ui.context_controller import (
    ContextController,
    ContextControllerPhase,
    ContextControllerState,
)
from codexbar.ui.context_viewmodel import (
    ContextPresenter,
    ContextViewKind,
    ContextViewState,
    ContextWindowViewState,
)


class HistoricalContextPanel(QFrame):
    """Async Historical Context surface; repository/summary work stays off Qt."""

    def __init__(
        self,
        controller: ContextController | ContextPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = (
            controller
            if isinstance(controller, ContextController)
            else ContextController(controller)
        )
        self._last_state: ContextControllerState | None = None
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Historical context"))
        explanation = QLabel(
            "Descriptive comparison with independent retained historical cycles "
            "at a similar time before reset."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self._body = QLabel("No current usage observation yet.")
        self._body.setWordWrap(True)
        layout.addWidget(self._body)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(25)
        self._poll_timer.timeout.connect(self._poll)

    def refresh(self) -> None:
        if self._controller.start():
            self.render_controller_state(self._controller.state)
        if self._controller.busy:
            self._poll_timer.start()

    def render_controller_state(self, state: ContextControllerState) -> None:
        self._last_state = state
        if state.phase is ContextControllerPhase.LOADING:
            self._body.setText(state.message or "Loading historical context…")
            return
        if state.phase is ContextControllerPhase.UNAVAILABLE:
            self._body.setText(
                f"{state.message or 'Historical context is unavailable.'}\n"
                "Comparable cycles: unavailable"
            )
            return
        self.render_state(state.view)

    def render_state(self, state: ContextViewState) -> None:
        if not state.windows:
            self._body.setText(
                "No current usage observation yet.\nComparable cycles: unavailable"
            )
            return
        self._body.setText("\n\n".join(_render_window(window) for window in state.windows))

    def _poll(self) -> None:
        state = self._controller.poll()
        if state != self._last_state:
            self.render_controller_state(state)
        if not self._controller.busy:
            self._poll_timer.stop()


def _render_window(window: ContextWindowViewState) -> str:
    lines = [
        window.label,
        f"  Coverage: {window.status_text}",
        f"  Comparable cycles: {_count_text(window.comparable_cycle_count)}",
    ]

    if window.kind is ContextViewKind.SPARSE:
        historical_range = f"{_percent(window.range_low)}–{_percent(window.range_high)}"
        lines.append(f"  Observed historical range: {historical_range}")
    elif window.kind is ContextViewKind.LIMITED:
        historical_range = f"{_percent(window.range_low)}–{_percent(window.range_high)}"
        lines.extend(
            (
                f"  Historical median: {_percent(window.median)}",
                f"  Observed historical range: {historical_range}",
            )
        )
    elif window.kind is ContextViewKind.ESTABLISHED:
        middle_50 = f"{_percent(window.band_low)}–{_percent(window.band_high)}"
        lines.extend(
            (
                f"  Historical median: {_percent(window.median)}",
                f"  Empirical middle 50%: {middle_50}",
            )
        )

    if window.rank_text is not None:
        lines.append(f"  {window.rank_text}")
    return "\n".join(lines)


def _percent(value: Decimal | None) -> str:
    if value is None:
        return "unavailable"
    return f"{format((value * Decimal('100')).normalize(), 'f')}%"


def _count_text(value: int | None) -> str:
    return "unavailable" if value is None else str(value)
