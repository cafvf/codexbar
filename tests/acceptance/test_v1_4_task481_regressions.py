from __future__ import annotations

from pathlib import Path


def test_current_card_exposes_state_as_separate_field() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    assert 'QLabel(f"State: {window.state.value.upper()}")' in source


def test_current_panel_exposes_freshness_explicitly() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    assert "Freshness: CURRENT" in source
    assert "Freshness: STALE" in source


def test_missing_reset_is_explicit_without_fabricating_time() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    assert 'QLabel("Reset: not reported")' in source


def test_details_panel_has_single_history_affordance_per_card() -> None:
    current = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )
    shell = Path("src/codexbar/ui/history_tray.py").read_text(
        encoding="utf-8"
    )

    assert 'QPushButton("View history"' in current
    assert 'QPushButton("History"' not in shell
    assert "history_button.clicked.connect(" in current
    assert "window_id=window.window_id" in current
    assert "self._open_history(window_id)" in current
