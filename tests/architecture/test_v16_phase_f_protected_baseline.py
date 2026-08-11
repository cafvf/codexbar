import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "src/codexbar/domain/models.py"
BUDGET = ROOT / "src/codexbar/application/budget.py"
ALERTS = ROOT / "src/codexbar/application/alerts.py"
RESET_MONITOR = ROOT / "src/codexbar/application/reset_monitor.py"
TRAY = ROOT / "src/codexbar/ui/tray.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imports_context(path: Path) -> bool:
    for node in ast.walk(_tree(path)):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module
            in {
                "codexbar.application.context",
                "codexbar.domain.context",
            }
        ):
            return True
        if isinstance(node, ast.Import) and any(
            alias.name
            in {
                "codexbar.application.context",
                "codexbar.domain.context",
            }
            for alias in node.names
        ):
            return True
    return False


def test_task_668_usage_snapshot_remains_context_free() -> None:
    tree = _tree(MODELS)
    usage_snapshot = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "UsageSnapshot"
    )
    names = {
        node.id
        for node in ast.walk(usage_snapshot)
        if isinstance(node, ast.Name)
    }

    assert not any(name.startswith("Context") for name in names)


def test_task_668_control_and_alert_policy_do_not_depend_on_context() -> None:
    assert not _imports_context(BUDGET)
    assert not _imports_context(ALERTS)
    assert not _imports_context(RESET_MONITOR)


def test_task_668_native_tray_glance_does_not_depend_on_context() -> None:
    assert not _imports_context(TRAY)
