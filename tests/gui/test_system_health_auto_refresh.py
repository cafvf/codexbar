from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from codexbar.ui.system_health_panel import SystemHealthDialog
from codexbar.ui.system_health_viewmodel import SystemHealthViewState


class _Presenter:
    def __init__(self) -> None:
        self.calls = 0

    def current(self) -> SystemHealthViewState:
        self.calls += 1
        return SystemHealthViewState(
            overall="healthy",
            overall_label="Healthy",
            overall_summary="Runtime is healthy.",
            generated_at=f"2026-08-14T15:30:0{self.calls}-03:00",
            subsystems=(),
            runtime_metrics=(),
        )


def _application() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication([])


def test_system_health_is_auto_refreshing_read_only_surface() -> None:
    app = _application()
    presenter = _Presenter()
    dialog = SystemHealthDialog(presenter)  # type: ignore[arg-type]

    button_texts = {
        button.text() for button in dialog.findChildren(QPushButton)
    }
    assert button_texts == {"Close"}
    assert not hasattr(dialog, "_refresh_status")
    assert not hasattr(dialog, "_refresh_button")
    assert not hasattr(dialog, "_manual_refresh")

    label_texts = {
        label.text() for label in dialog.findChildren(QLabel)
    }
    assert "Updates automatically while this window is open." in label_texts

    dialog.refresh()
    app.processEvents()

    assert presenter.calls == 1
    assert "Healthy" in dialog.panel._summary.text()

    dialog.close()
