import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSITION = ROOT / "src/codexbar/composition.py"
MAIN = ROOT / "src/codexbar/__main__.py"
PANEL = ROOT / "src/codexbar/ui/control_panel.py"
PRESENTER = ROOT / "src/codexbar/ui/current_account_viewmodel.py"
CONTEXT = ROOT / "src/codexbar/application/context.py"
HISTORY_RUNTIME = ROOT / "src/codexbar/application/history_runtime.py"
HISTORY_POLICY = ROOT / "src/codexbar/application/history_policy.py"
HISTORY_REPOSITORY = ROOT / "src/codexbar/infrastructure/history_sqlite.py"
RESET_REPOSITORY = ROOT / "src/codexbar/infrastructure/reset_event_sqlite.py"
STORAGE_CONTRACTS = ROOT / "src/codexbar/infrastructure/storage_contracts.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imported_names(path: Path, module: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def _attribute_assignments(path: Path) -> set[tuple[str, str]]:
    assignments: set[tuple[str, str]] = set()
    for node in ast.walk(_tree(path)):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets.extend(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets.append(node.target)
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
            ):
                assignments.add((target.value.id, target.attr))
    return assignments


def _run_tray_context_keyword_is_explicit() -> bool:
    for node in ast.walk(_tree(MAIN)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "run_tray":
            continue
        for keyword in node.keywords:
            value = keyword.value
            if (
                keyword.arg == "context_presenter"
                and isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id == "runtime"
                and value.attr == "context_presenter"
            ):
                return True
    return False


def test_context_presenter_has_one_explicit_wiring_path() -> None:
    assert ("presenter", "context_presenter") not in _attribute_assignments(COMPOSITION)
    assert _run_tray_context_keyword_is_explicit()

    panel_calls = {
        node.func.id
        for node in ast.walk(_tree(PANEL))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "getattr" not in panel_calls

    presenter_names = {
        node.id
        for node in ast.walk(_tree(PRESENTER))
        if isinstance(node, ast.Name)
    }
    assert "context_presenter" not in presenter_names


def test_history_retention_has_one_policy_owner() -> None:
    assert _imported_names(
        CONTEXT,
        "codexbar.application.history_policy",
    ) == {"HISTORY_RETENTION"}
    assert _imported_names(
        HISTORY_RUNTIME,
        "codexbar.application.history_policy",
    ) == {"HISTORY_RETENTION"}

    assignments = [
        node
        for node in _tree(HISTORY_POLICY).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "HISTORY_RETENTION"
            for target in node.targets
        )
    ]
    assert len(assignments) == 1


def test_sqlite_contracts_are_owned_by_repositories() -> None:
    assert not STORAGE_CONTRACTS.exists()

    for path in (HISTORY_REPOSITORY, RESET_REPOSITORY):
        method_names = {
            node.name
            for node in ast.walk(_tree(path))
            if isinstance(node, ast.FunctionDef)
        }
        assert "_validate_operational_contract" in method_names

    composition_imports = {
        node.module
        for node in ast.walk(_tree(COMPOSITION))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "codexbar.infrastructure.storage_contracts" not in composition_imports
