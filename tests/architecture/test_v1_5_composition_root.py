import ast
from pathlib import Path

import codexbar.composition as composition

ROOT = Path(__file__).resolve().parents[2]
COMPOSITION = ROOT / "src/codexbar/composition.py"
MAIN = ROOT / "src/codexbar/__main__.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            result.add(node.module)
        elif isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
    return result


def test_composition_root_is_headless_import_safe() -> None:
    imports = _imports(COMPOSITION)

    assert not any(name.startswith("PySide6") for name in imports)
    assert hasattr(composition, "build_gui_runtime")
    assert hasattr(composition, "build_usage_provider")


def test_main_delegates_gui_wiring_to_composition_root() -> None:
    source = MAIN.read_text()

    assert "build_gui_runtime" in source
    assert "NotifySendNotificationAdapter" not in source
    assert "open_history_analytics_repository" not in source
