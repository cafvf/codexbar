from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_CONTEXT = Path("src/codexbar/domain/context.py")
FORBIDDEN_CALL_NAMES = {
    "forecast",
    "regression",
    "eta",
    "probability_of_exhaustion",
    "prediction_interval",
}


def test_phase_c_statistics_have_no_external_numeric_dependency() -> None:
    tree = ast.parse(DOMAIN_CONTEXT.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])

    assert "numpy" not in imported_roots
    assert "pandas" not in imported_roots
    assert "scipy" not in imported_roots


def test_phase_c_context_domain_exposes_no_predictive_api_names() -> None:
    tree = ast.parse(DOMAIN_CONTEXT.read_text(encoding="utf-8"))
    defined_names = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }

    assert defined_names.isdisjoint(FORBIDDEN_CALL_NAMES)
