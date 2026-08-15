from __future__ import annotations

import ast
from pathlib import Path

PLAN = Path("src/codexbar/application/plan.py")
SETTINGS = Path("src/codexbar/domain/settings.py")
BUDGET = Path("src/codexbar/application/budget.py")
SRC = Path("src/codexbar")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _class_fields(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            }
    raise AssertionError(f"class {class_name} not found in {path}")


def _string_literals(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def test_inv_plan_001_core_has_no_history_or_context_authority_dependency() -> None:
    modules = _imported_modules(PLAN)

    assert not any("history" in module for module in modules)
    assert not any(module.endswith(".context") for module in modules)


def test_inv_plan_002_and_003_core_has_no_persistence_or_concurrency_subsystem() -> None:
    modules = _imported_modules(PLAN)
    source = PLAN.read_text(encoding="utf-8")

    assert not any(module.startswith("codexbar.infrastructure") for module in modules)
    assert not any(
        module in {"sqlite3", "asyncio", "threading"}
        or module.startswith("concurrent")
        for module in modules
    )
    assert "PlanRepository" not in source
    assert "PlanRuntime" not in source
    assert "QTimer" not in source
    assert "ThreadPool" not in source

    forbidden_paths = {
        "plan_repository.py",
        "plan_store.py",
        "plan_cache.py",
        "plan_runtime.py",
    }
    assert not any(path.name in forbidden_paths for path in SRC.rglob("*.py"))


def test_inv_plan_004_core_has_no_redeem_or_account_mutation_path() -> None:
    modules = _imported_modules(PLAN)
    source = PLAN.read_text(encoding="utf-8")

    assert "codexbar.application.redeem" not in modules
    assert "codexbar.application.account" not in modules
    assert "codexbar.domain.reset" not in modules
    assert "consume_reset_credit" not in source
    assert "RedeemProcessManager" not in source


def test_inv_plan_005_checkpoint_model_does_not_duplicate_reserve() -> None:
    fields = _class_fields(SETTINGS, "UsagePlanCheckpoint")

    assert fields == {"window_id", "time_to_reset", "minimum_remaining"}


def test_inv_plan_006_budget_remains_plan_independent() -> None:
    modules = _imported_modules(BUDGET)
    source = BUDGET.read_text(encoding="utf-8")

    assert "codexbar.application.plan" not in modules
    assert "UsagePlanCheckpoint" not in source
    assert "PlanCompliance" not in source


def test_inv_plan_007_window_identity_remains_opaque() -> None:
    literals = _string_literals(PLAN) + _string_literals(SETTINGS)
    source = PLAN.read_text(encoding="utf-8") + SETTINGS.read_text(encoding="utf-8")

    assert not any("windowDurationMins" in literal for literal in literals)
    assert not any(literal.startswith("window_") for literal in literals)
    assert ".split(" not in source
    assert "parse_duration" not in source


def test_plan_uses_shared_neutral_quantities() -> None:
    plan_modules = _imported_modules(PLAN)
    settings_modules = _imported_modules(SETTINGS)

    assert "codexbar.domain.quantities" in plan_modules
    assert "codexbar.domain.quantities" in settings_modules
