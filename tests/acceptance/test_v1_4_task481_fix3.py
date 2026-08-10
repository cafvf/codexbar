from __future__ import annotations

from pathlib import Path


def test_history_window_identity_is_internal_not_a_visible_selector() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    assert "_focused_window_id: UsageWindowId | None" in source
    assert "window_id=self._focused_window_id" in source
    assert 'QLabel("Window:")' not in source


def test_history_does_not_mutate_combo_window_labels() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    assert "setItemText(index, state.selected_label)" not in source
    assert "window_combo" not in source


def test_history_status_exposes_selected_stable_identity() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(
        encoding="utf-8"
    )

    assert 'text = f"Observed history — {selected} [{identity}]"' in source
