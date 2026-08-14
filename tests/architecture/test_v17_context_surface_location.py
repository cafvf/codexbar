from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_historical_context_is_composed_with_history_without_coupling_history_base() -> None:
    details = _source("src/codexbar/ui/control_panel.py")
    history_dialog = _source("src/codexbar/ui/history_dialog.py")
    history_tray = _source("src/codexbar/ui/history_tray.py")
    composition = _source("src/codexbar/ui/context_history_dialog.py")
    control_tray = _source("src/codexbar/ui/control_tray.py")

    assert "HistoricalContextPanel" not in details
    assert "HistoricalContextPanel" not in history_dialog
    assert "HistoricalContextPanel" not in history_tray
    assert "ContextController" not in history_dialog
    assert "ContextController" not in history_tray

    assert "class ContextHistoryDialog(HistoryDialog)" in composition
    assert "HistoricalContextPanel" in composition
    assert "self._context_panel.refresh()" in composition
    assert "ContextHistoryDialog" in control_tray
