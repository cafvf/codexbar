from __future__ import annotations

from pathlib import Path


def test_view_history_button_uses_clicked_signal_with_stable_identity() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    assert "history_button.clicked.connect(" in source
    assert "window_id=window.window_id" in source
    assert "self._open_history(window_id)" in source


def test_history_period_change_does_not_render_transient_loading_state() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    period_start = source.index("def _period_changed")
    loading_start = source.index("def _set_loading_status")
    handler = source[period_start:loading_start]

    assert "self.render_state(self._controller.state)" not in handler
    assert handler.count("self._set_loading_status()") == 1


def test_history_loading_feedback_does_not_rewrite_period_selector() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    start = source.index("def _set_loading_status")
    end = source.index("def _selected_period", start)
    block = source[start:end]

    assert "period_combo" not in block
