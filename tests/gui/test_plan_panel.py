import os
from typing import Any, cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from codexbar.ui.control_panel import CurrentAccountPanel  # noqa: E402


class FakePresenter:
    def current(self) -> None:
        return None


def test_plan_panel_is_between_budget_and_redeem_without_replacing_existing_panels() -> None:
    app = QApplication.instance() or QApplication([])
    panel = CurrentAccountPanel(cast(Any, FakePresenter()), None)

    reset_index = panel._layout.indexOf(panel.reset_panel)
    budget_index = panel._layout.indexOf(panel.budget_panel)
    plan_index = panel._layout.indexOf(panel.plan_panel)
    redeem_index = panel._layout.indexOf(panel.redeem_panel)

    assert reset_index < budget_index < plan_index < redeem_index
    assert plan_index == budget_index + 1
    assert redeem_index == plan_index + 1

    panel.close()
    app.processEvents()
