from __future__ import annotations

from pathlib import Path


def test_current_panel_does_not_parse_provider_or_read_history() -> None:
    source = Path("src/codexbar/ui/current_panel.py").read_text(
        encoding="utf-8"
    )

    forbidden = (
        "sqlite3",
        "history_sqlite",
        "HistoricalAnalysisService",
        "CodexAppServerProvider",
        "provider payload",
    )
    assert not any(item in source for item in forbidden)


def test_current_to_history_navigation_uses_identity_not_label() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(
        encoding="utf-8"
    )

    assert "show_history_for_window" in source
    assert "UsageWindowId" in source
    assert "dialog.open_history(window_id=window_id)" in source


def test_native_helper_boundary_contains_no_history_data() -> None:
    helper = Path("src/codexbar/ui/native_indicator_helper.py").read_text(
        encoding="utf-8"
    )

    assert "HistoricalWindowSample" not in helper
    assert "history.sqlite3" not in helper
    assert "remaining" not in helper.lower() or "set_glance" in helper


def test_v1_3_current_tray_module_stays_free_of_historical_analytics() -> None:
    source = Path("src/codexbar/ui/tray.py").read_text(encoding="utf-8")

    assert "HistoricalAnalysisService" not in source
    assert "HistoryController" not in source
    assert "history_sqlite" not in source
