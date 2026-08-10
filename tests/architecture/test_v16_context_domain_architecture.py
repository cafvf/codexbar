from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_CONTEXT = Path("src/codexbar/domain/context.py")


def test_task_629_context_domain_has_no_sqlite_or_qt_dependency() -> None:
    tree = ast.parse(DOMAIN_CONTEXT.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])

    assert "sqlite3" not in imported_roots
    assert "PySide6" not in imported_roots
    assert "gi" not in imported_roots


def test_task_629_context_domain_does_not_import_infrastructure_or_ui_layers() -> None:
    source = DOMAIN_CONTEXT.read_text(encoding="utf-8")

    assert "codexbar.infrastructure" not in source
    assert "codexbar.ui" not in source
