from __future__ import annotations

import ast
from pathlib import Path


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_historical_ui_has_no_sqlite_implementation_import() -> None:
    for name in (
        "history_dialog.py",
        "history_tray.py",
        "history_viewmodel.py",
        "history_controller.py",
    ):
        modules = imported_modules(Path("src/codexbar/ui") / name)
        assert "sqlite3" not in modules
        assert "codexbar.infrastructure.history_sqlite" not in modules


def test_composition_root_owns_history_storage_wiring() -> None:
    source = Path("src/codexbar/composition.py").read_text(encoding="utf-8")
    assert "open_history_analytics_repository" in source
    assert "HistoricalAnalysisService" in source
    assert "HistoryController" in source


def test_validated_tray_module_is_not_replaced_by_history_feature() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")
    assert "class HistoricalTrayShell(TrayShell)" in source
    assert "from codexbar.ui.tray import TrayShell" in source


def test_history_navigation_sends_no_data_to_native_helper() -> None:
    source = Path("src/codexbar/ui/history_tray.py").read_text(encoding="utf-8")
    assert "NativeIndicator" not in source
    assert "set_glance" not in source
    assert "raw_payload" not in source
