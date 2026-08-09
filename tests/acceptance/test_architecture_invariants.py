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


def test_ac_usage_009_ui_does_not_import_infrastructure() -> None:
    for path in Path("src/codexbar/ui").rglob("*.py"):
        assert not any(
            module.startswith("codexbar.infrastructure") for module in imported_modules(path)
        ), path


def test_inv_arch_001_domain_does_not_import_outer_layers() -> None:
    forbidden = ("codexbar.application", "codexbar.infrastructure", "codexbar.ui")
    for path in Path("src/codexbar/domain").rglob("*.py"):
        assert not any(module.startswith(forbidden) for module in imported_modules(path)), path


def test_inv_alert_001_alert_core_does_not_import_ui_or_platform_implementations() -> None:
    path = Path("src/codexbar/application/alerts.py")
    forbidden = (
        "PySide6",
        "gi",
        "dbus",
        "subprocess",
        "codexbar.infrastructure",
        "codexbar.ui",
    )

    assert not any(module.startswith(forbidden) for module in imported_modules(path))


def test_inv_alert_002_alert_core_reuses_usage_window_state_classifier() -> None:
    path = Path("src/codexbar/application/alerts.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    calls_state = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "state"
        for node in ast.walk(tree)
    )
    comparisons_to_fraction_value = any(
        isinstance(node, ast.Attribute) and node.attr == "value"
        for node in ast.walk(tree)
    )

    assert calls_state
    assert not comparisons_to_fraction_value


def test_inv_alert_003_notification_transport_is_confined_to_infrastructure() -> None:
    transport = Path("src/codexbar/infrastructure/notifications.py")
    assert any(module.startswith("PySide6.QtDBus") for module in imported_modules(transport))

    for layer in ("domain", "application", "ui"):
        for path in Path(f"src/codexbar/{layer}").rglob("*.py"):
            assert not any(
                module.startswith("PySide6.QtDBus") for module in imported_modules(path)
            ), path
