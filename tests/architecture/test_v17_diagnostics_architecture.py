from __future__ import annotations

import ast
from pathlib import Path

DOMAIN = Path("src/codexbar/domain/diagnostics.py")
APPLICATION = Path("src/codexbar/application/diagnostics.py")
INFRASTRUCTURE = Path("src/codexbar/infrastructure/diagnostics.py")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def test_diagnostics_domain_is_framework_and_infrastructure_independent() -> None:
    roots = imported_roots(DOMAIN)
    source = DOMAIN.read_text(encoding="utf-8")

    assert roots.isdisjoint({"sqlite3", "subprocess", "PySide6", "gi"})
    assert "codexbar.infrastructure" not in source
    assert "codexbar.ui" not in source


def test_diagnostics_application_layer_has_no_qt_or_destructive_redeem_dependency() -> None:
    source = APPLICATION.read_text(encoding="utf-8")

    assert "PySide6" not in source
    assert "codexbar.ui" not in source
    assert "reset_consumer" not in source
    assert "RedeemProcessManager" not in source


def test_lineage_diagnostics_do_not_read_private_auth_or_jwt_storage() -> None:
    source = INFRASTRUCTURE.read_text(encoding="utf-8").lower()

    assert "auth.json" not in source
    assert "decode_jwt" not in source
    assert "jwt" not in source
    assert "codexresetcreditconsumer" not in source
    assert "reset_consumer" not in source
