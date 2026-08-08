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
