from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from codexbar.ui.context_viewmodel import (
    ContextPresenter,
    ContextViewKind,
    ContextViewState,
    ContextWindowViewState,
)


class HistoricalContextPanel(QFrame):
    """Visually distinct descriptive Historical Context section for Open Details."""

    def __init__(
        self,
        presenter: ContextPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        title = QLabel("Historical context")
        layout.addWidget(title)
        explanation = QLabel(
            "Descriptive comparison with independent retained historical cycles "
            "at a similar time before reset."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self._body = QLabel("No current usage observation yet.")
        self._body.setWordWrap(True)
        layout.addWidget(self._body)

    def refresh(self) -> None:
        self.render_state(self._presenter.current())

    def render_state(self, state: ContextViewState) -> None:
        if not state.windows:
            self._body.setText(
                "No current usage observation yet.\nComparable cycles: unavailable"
            )
            return

        blocks = [_render_window(window) for window in state.windows]
        self._body.setText("\n\n".join(blocks))


def _render_window(window: ContextWindowViewState) -> str:
    lines = [
        window.label,
        f"  Coverage: {window.status_text}",
        f"  Comparable cycles: {_count_text(window.comparable_cycle_count)}",
    ]

    if window.kind is ContextViewKind.SPARSE:
        historical_range = (
            f"{_percent(window.range_low)}–{_percent(window.range_high)}"
        )
        lines.append(f"  Observed historical range: {historical_range}")
    elif window.kind is ContextViewKind.LIMITED:
        historical_range = (
            f"{_percent(window.range_low)}–{_percent(window.range_high)}"
        )
        lines.extend(
            (
                f"  Historical median: {_percent(window.median)}",
                f"  Observed historical range: {historical_range}",
            )
        )
    elif window.kind is ContextViewKind.ESTABLISHED:
        middle_50 = (
            f"{_percent(window.band_low)}–{_percent(window.band_high)}"
        )
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
