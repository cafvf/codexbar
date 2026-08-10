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


def called_attributes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def test_inv_history_001_domain_has_no_history_storage_dependency() -> None:
    forbidden = (
        "sqlite3",
        "pathlib",
        "codexbar.infrastructure",
    )
    for path in Path("src/codexbar/domain").rglob("*.py"):
        modules = imported_modules(path)
        assert not any(module.startswith(forbidden) for module in modules), path


def test_inv_history_002_history_application_has_no_qt_ui_or_sqlite_dependency() -> None:
    forbidden = (
        "PySide6",
        "sqlite3",
        "codexbar.infrastructure",
        "codexbar.ui",
    )
    for name in ("history.py", "history_runtime.py"):
        path = Path("src/codexbar/application") / name
        modules = imported_modules(path)
        assert not any(module.startswith(forbidden) for module in modules), path


def test_inv_history_003_current_usage_is_not_read_from_history_repository() -> None:
    runtime = Path("src/codexbar/application/history_runtime.py")
    calls = called_attributes(runtime)

    assert "append" in calls
    assert "prune" in calls
    assert "query" not in calls
    assert "query_window" not in calls
    assert "inspect" not in calls


def test_inv_history_004_stale_guard_exists_before_history_append() -> None:
    path = Path("src/codexbar/application/history_runtime.py")
    source = path.read_text(encoding="utf-8")

    stale_guard = source.index("snapshot.freshness is not Freshness.CURRENT")
    append = source.index("self._repository.append")

    assert stale_guard < append


def test_inv_history_005_settings_storage_does_not_import_history() -> None:
    paths = (
        Path("src/codexbar/domain/settings.py"),
        Path("src/codexbar/application/settings.py"),
        Path("src/codexbar/infrastructure/settings.py"),
    )
    for path in paths:
        assert not any(
            module.startswith(
                (
                    "codexbar.application.history",
                    "codexbar.infrastructure.history",
                )
            )
            for module in imported_modules(path)
        ), path


def test_inv_history_006_sqlite_adapter_consumes_normalized_history_contract() -> None:
    path = Path("src/codexbar/infrastructure/history_sqlite.py")
    source = path.read_text(encoding="utf-8")

    forbidden_names = (
        "raw_payload",
        "credentials",
        "account_id",
        "access_token",
    )
    assert not any(name in source for name in forbidden_names)


def test_inv_history_007_refresh_core_does_not_depend_on_history_storage() -> None:
    path = Path("src/codexbar/application/refresh.py")
    modules = imported_modules(path)

    assert not any("history" in module for module in modules)
    assert not any(module.startswith("codexbar.infrastructure") for module in modules)


def test_inv_history_008_clear_is_not_used_as_corruption_recovery() -> None:
    path = Path("src/codexbar/infrastructure/history_sqlite.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    exception_handlers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
    ]
    for handler in exception_handlers:
        calls = {
            node.func.attr
            for node in ast.walk(handler)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert "clear" not in calls
        assert "unlink" not in calls


def test_perf_guard_history_storage_is_not_called_from_ui_controller() -> None:
    path = Path("src/codexbar/ui/controller.py")
    modules = imported_modules(path)
    source = path.read_text(encoding="utf-8")

    assert not any("history" in module for module in modules)
    assert "HistoryService" not in source
    assert "SqliteHistoryRepository" not in source


def test_history_concrete_storage_is_confined_to_composition_and_infrastructure() -> None:
    allowed_files = {
        Path("src/codexbar/__main__.py"),
        Path("src/codexbar/composition.py"),
    }
    infrastructure_root = Path("src/codexbar/infrastructure")

    for path in Path("src/codexbar").rglob("*.py"):
        if path in allowed_files or path.is_relative_to(infrastructure_root):
            continue
        source = path.read_text(encoding="utf-8")
        assert "SqliteHistoryRepository" not in source, path
