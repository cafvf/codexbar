from __future__ import annotations

import ast
from pathlib import Path

APPLICATION_CONTEXT = Path("src/codexbar/application/context.py")
COMPOSITION = Path("src/codexbar/composition.py")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_task_646_context_application_has_no_upstream_account_reader_dependency() -> None:
    source = APPLICATION_CONTEXT.read_text(encoding="utf-8")

    assert "AccountRateLimitsReader" not in source
    assert "read_account_rate_limits" not in source
    assert "UsageProvider" not in source
    assert "get_usage" not in source


def test_task_640_application_context_has_no_infrastructure_or_ui_dependency() -> None:
    modules = _imported_modules(APPLICATION_CONTEXT)

    assert not any(module.startswith("codexbar.infrastructure") for module in modules)
    assert not any(module.startswith("codexbar.ui") for module in modules)
    assert "sqlite3" not in modules


def test_task_649_composition_root_wires_context_service_through_adapter() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")

    assert "HistoricalContextService" in source
    assert "SqliteContextHistoryRepository" in source
    assert "context_service=context_service" in source
