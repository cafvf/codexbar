from __future__ import annotations

from pathlib import Path


def test_history_period_selector_uses_stable_primitive_values() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(encoding="utf-8")

    assert "self.period_combo.addItem(label, period.value)" in source
    assert "AnalysisPeriod(str(value))" in source
    assert 'QLabel("Window:")' not in source
    assert "window_combo" not in source


def test_history_chart_has_intermediate_vertical_scale() -> None:
    source = Path("src/codexbar/ui/history_dialog.py").read_text(encoding="utf-8")

    assert "for percent in (0, 25, 50, 75, 100):" in source
    assert "QPalette.ColorRole.Highlight" in source


def test_successful_current_refresh_rereads_only_visible_history() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")

    assert "_history_reload_after_current" not in source
    assert "previous.phase is not TrayPhase.LOADING" in source
    assert "current.phase is not TrayPhase.FRESH" in source
    assert "dialog.isVisible()" in source
    assert "dialog.refresh()" in source
