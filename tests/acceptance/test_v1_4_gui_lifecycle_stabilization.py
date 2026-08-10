from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from codexbar.ui.controller import TrayPhase, TrayViewState
from codexbar.ui.tray import TrayShell


class PanelSpy:
    def __init__(self) -> None:
        self.states: list[TrayViewState] = []

    def render_state(self, state: TrayViewState) -> None:
        self.states.append(state)


def test_unchanged_current_state_is_not_rendered_twice() -> None:
    shell = TrayShell.__new__(TrayShell)
    panel = PanelSpy()
    shell._panel = panel
    shell._last_rendered_state = None
    shell._native_indicator = None
    shell._tray = None
    shell._summary_action = SimpleNamespace(setText=lambda _text: None)

    state = TrayViewState(phase=TrayPhase.LOADING)
    shell._apply_state(state)
    shell._apply_state(state)

    assert panel.states == [state]


def test_history_is_not_owned_by_current_panel() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")

    assert "HistoryDialog(self._history_controller)" in source
    assert "HistoryDialog(self._history_controller, self._panel)" not in source
    assert "legacy_panel" not in source
    assert "deleteLater()" not in source


def test_tray_shell_accepts_composed_panel() -> None:
    source = Path("src/codexbar/ui/tray.py").read_text(encoding="utf-8")

    assert "panel: UsagePanel | None = None" in source
    assert "self._panel = panel or UsagePanel()" in source
    assert "if state == self._last_rendered_state" in source


def test_current_poll_does_not_give_tray_controller_history_dependency() -> None:
    source = Path("src/codexbar/ui/controller.py").read_text(encoding="utf-8")

    assert "HistoryController" not in source
    assert "HistoryRepository" not in source
    assert "history_sqlite" not in source
