from __future__ import annotations

import ast
from pathlib import Path


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_analytics_has_no_qt_sqlite_or_infrastructure_dependency() -> None:
    path = Path("src/codexbar/application/analytics.py")
    modules = imports(path)
    forbidden = ("PySide6", "sqlite3", "codexbar.infrastructure", "codexbar.ui")
    assert not any(module.startswith(forbidden) for module in modules)


def test_analytics_source_contains_no_history_mutation_calls() -> None:
    source = Path("src/codexbar/application/analytics.py").read_text(encoding="utf-8")
    for mutation in (".append(", ".prune(", ".clear("):
        assert mutation not in source


def test_schema_version_remains_one() -> None:
    source = Path("src/codexbar/infrastructure/history_sqlite.py").read_text(encoding="utf-8")
    assert "_SCHEMA_VERSION = 1" in source
    assert "_SCHEMA_VERSION = 2" not in source


def test_window_discovery_uses_dedicated_distinct_query() -> None:
    source = Path("src/codexbar/infrastructure/history_sqlite.py").read_text(
        encoding="utf-8"
    )
    method = source[source.index("    def list_window_ids("):source.index("    def prune(")]
    assert "SELECT DISTINCT w.window_id" in method
    assert "self.query(" not in method
