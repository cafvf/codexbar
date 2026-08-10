from __future__ import annotations

from pathlib import Path


def test_native_helper_exposes_history_action() -> None:
    source = Path(
        "src/codexbar/ui/native_indicator_helper.py"
    ).read_text(encoding="utf-8")

    assert '("History", "history")' in source
    assert 'Gtk.MenuItem(label="History")' in source
    assert '_emit("history")' in source


def test_historical_tray_binds_native_history_event() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(
        encoding="utf-8"
    )

    assert 'native_indicator._callbacks["history"] = self.show_history' in source
    assert "raw_payload" not in source
    assert "HistoricalWindowSample" not in source


def test_history_action_carries_only_ui_intent() -> None:
    helper = Path(
        "src/codexbar/ui/native_indicator_helper.py"
    ).read_text(encoding="utf-8")

    assert '{"event": event}' in helper
    assert "window_id" not in helper
    assert "history.sqlite3" not in helper
