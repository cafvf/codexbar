import ast
from dataclasses import fields
from pathlib import Path

from codexbar.application.account import AccountRateLimitsReader, ResetCreditConsumer
from codexbar.domain.models import UsageSnapshot

ROOT = Path(__file__).resolve().parents[2]
ACCOUNT_MODULE = ROOT / "src/codexbar/application/account.py"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    return imported


def test_usage_snapshot_remains_reset_credit_free() -> None:
    names = {field.name for field in fields(UsageSnapshot)}

    assert "reset_credits" not in names
    assert not any("reset" in name for name in names)


def test_account_application_boundary_has_no_ui_or_infrastructure_imports() -> None:
    imported = _imported_modules(ACCOUNT_MODULE)

    assert not any(name.startswith("codexbar.infrastructure") for name in imported)
    assert not any(name.startswith("codexbar.ui") for name in imported)


def test_reader_and_destructive_consumer_are_interface_segregated() -> None:
    assert AccountRateLimitsReader is not ResetCreditConsumer
    assert "read_account_rate_limits" in AccountRateLimitsReader.__dict__
    assert "read_account_rate_limits" not in ResetCreditConsumer.__dict__
