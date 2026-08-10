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


def test_history_viewmodel_has_no_sqlite_or_provider_dependency() -> None:
    modules = imported_modules(Path("src/codexbar/ui/history_viewmodel.py"))
    assert "sqlite3" not in modules
    assert not any(module.startswith("codexbar.infrastructure") for module in modules)


def test_history_controller_has_no_sqlite_dependency() -> None:
    modules = imported_modules(Path("src/codexbar/ui/history_controller.py"))
    assert "sqlite3" not in modules
    assert not any(module.startswith("codexbar.infrastructure") for module in modules)


def test_existing_current_controller_is_not_modified_for_history_reads() -> None:
    path = Path("src/codexbar/ui/controller.py")
    if path.exists():
        source = path.read_text(encoding="utf-8")
        assert "HistoricalAnalysisService" not in source
        assert "SqliteHistoryRepository" not in source
