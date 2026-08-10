from __future__ import annotations

from pathlib import Path


def test_current_panel_has_no_history_storage_dependency() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(encoding="utf-8")

    assert "history_sqlite" not in source
    assert "HistoricalAnalysisService" not in source


def test_history_navigation_uses_stable_window_id() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")

    assert "show_history_for_window" in source
    assert "dialog.open_history(window_id=window_id)" in source
    assert "label matching" not in source.lower()


def test_rich_current_panel_replaces_legacy_panel_only_in_historical_shell() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")

    assert "RichUsagePanel" in source
    assert "legacy_panel = self._panel" not in source
    assert "panel=panel" in source.replace(" ", "")
