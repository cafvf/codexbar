from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def test_instance_protocol_application_layer_has_no_qt_dependency() -> None:
    path = ROOT / "src/codexbar/application/instance_ownership.py"
    imports = _imports(path)
    assert not any(name.startswith("PySide6") for name in imports)
    assert not any(name.startswith("codexbar.ui") for name in imports)


def test_instance_qt_adapter_isolated_to_ui_layer() -> None:
    path = ROOT / "src/codexbar/ui/instance_ownership.py"
    imports = _imports(path)
    assert any(name.startswith("PySide6") for name in imports)


def test_gui_entrypoint_resolves_ownership_before_runtime_build() -> None:
    source = (ROOT / "src/codexbar/__main__.py").read_text()
    resolve_index = source.index("ownership = resolve_gui_instance()")
    build_index = source.index("runtime = build_gui_runtime(mock=args.mock)")
    assert resolve_index < build_index


def test_instance_adapter_retains_qapplication_for_owner_lifecycle() -> None:
    source = (ROOT / "src/codexbar/ui/instance_ownership.py").read_text()
    assert "_APPLICATION: QApplication | None = None" in source
    assert "_APPLICATION = app" in source
