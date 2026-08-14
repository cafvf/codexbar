from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from codexbar.domain.models import UsageWindowId
from codexbar.ui.context_controller import ContextController
from codexbar.ui.context_panel import HistoricalContextPanel
from codexbar.ui.history_controller import HistoryController
from codexbar.ui.history_dialog import HistoryDialog


class ContextHistoryDialog(HistoryDialog):
    """v1.7 composition: Usage History plus asynchronous Historical Context."""

    def __init__(
        self,
        history_controller: HistoryController,
        context_controller: ContextController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(history_controller, parent)
        self._context_panel = HistoricalContextPanel(context_controller, self)
        layout = self.layout()
        if not isinstance(layout, QVBoxLayout):
            raise RuntimeError("HistoryDialog must use QVBoxLayout")
        chart_index = layout.indexOf(self.chart)
        if chart_index < 0:
            layout.addWidget(self._context_panel)
        else:
            layout.insertWidget(chart_index, self._context_panel)

    def open_history(
        self,
        *,
        window_id: UsageWindowId | None = None,
    ) -> None:
        super().open_history(window_id=window_id)
        self._context_panel.refresh()

    def refresh(self) -> None:
        super().refresh()
        self._context_panel.refresh()
