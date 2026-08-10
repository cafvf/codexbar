from __future__ import annotations

from pathlib import Path


def test_history_exposes_period_as_only_selector() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    assert 'QLabel("Period:")' in source
    assert 'QLabel("Window:")' not in source
    assert "window_combo" not in source


def test_history_keeps_window_identity_internal() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    assert "_focused_window_id: UsageWindowId | None" in source
    assert "window_id=self._focused_window_id" in source
    assert "self._focused_window_id = state.selected_window_id" in source


def test_card_navigation_uses_clicked_signal_and_stable_identity() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    assert "history_button.clicked.connect(" in source
    assert "window_id=window.window_id" in source
    assert "self._open_history(window_id)" in source
