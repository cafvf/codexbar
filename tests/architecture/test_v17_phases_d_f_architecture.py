from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _calls(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
    return calls


def test_task_744_745_qt_context_panel_never_runs_presenter_current() -> None:
    source = _source("src/codexbar/ui/context_panel.py")
    assert "ContextController" in source
    assert ".current(" not in source
    assert "query_candidates" not in source
    assert "HistoricalContextService" not in source


def test_task_752_external_redeem_is_not_called_directly_from_qt_panel() -> None:
    calls = _calls("src/codexbar/ui/control_panel.py")
    assert "redeem" not in calls
    assert "retry" not in calls
    assert "start_redeem" in calls
    assert "start_retry" in calls


def test_task_759_no_automatic_redeem_start_in_composition() -> None:
    source = _source("src/codexbar/composition.py")
    assert "RedeemExecutionController" in source
    assert ".start_redeem(" not in source
    assert ".start_retry(" not in source


def test_task_761_health_panel_has_no_persistent_or_external_probe_imports() -> None:
    source = _source("src/codexbar/ui/system_health_panel.py")
    assert "infrastructure" not in source
    assert "Sqlite" not in source
    assert "CodexAccount" not in source


def test_task_761_system_health_is_separate_from_open_details() -> None:
    details = _source("src/codexbar/ui/control_panel.py")
    tray = _source("src/codexbar/ui/control_tray.py")
    helper = _source("src/codexbar/ui/native_indicator_helper.py")

    assert "SystemHealthPanel" not in details
    assert "health_presenter" not in details
    assert 'QAction("System health"' in tray
    assert "SystemHealthDialog" in tray
    assert 'Gtk.MenuItem(label="System health")' in helper
    assert '_emit("health")' in helper


def test_task_766_native_width_guide_has_no_fixed_5h_weekly_literal() -> None:
    source = _source("src/codexbar/ui/native_indicator.py")
    assert "NATIVE_LABEL_GUIDE" not in source
    assert '"5h:' not in source
    assert '"W:' not in source


def test_task_767_reset_monitor_is_not_owned_by_gui_composition() -> None:
    source = _source("src/codexbar/composition.py")
    assert "ResetExpiryMonitor" not in source
    reset_source = _source("src/codexbar/application/reset_monitor.py")
    assert "RESET_MONITOR_PRODUCTION_ACTIVE: Final = False" in reset_source
