import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from codexbar.ui.controller import TrayPhase, TrayViewState  # noqa: E402
from codexbar.ui.tray import UsagePanel, create_codexbar_icon  # noqa: E402


def test_usage_panel_renders_loading_state() -> None:
    app = QApplication.instance() or QApplication([])
    panel = UsagePanel()
    panel.render_state(TrayViewState(phase=TrayPhase.LOADING))
    assert panel._status.text() == "Refreshing…"
    assert panel.refresh_button.text() == "Refresh"
    assert panel.quit_button.text() == "Quit"
    panel.close()
    app.processEvents()


def test_ac_ui_009_project_icon_is_renderable() -> None:
    app = QApplication.instance() or QApplication([])
    icon = create_codexbar_icon()
    assert icon.isNull() is False
    assert icon.pixmap(32, 32).isNull() is False
    app.processEvents()
