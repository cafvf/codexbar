from __future__ import annotations

import ast
from pathlib import Path

PLAN = Path("src/codexbar/application/plan.py")
PLAN_ALERTS = Path("src/codexbar/application/plan_alerts.py")
SETTINGS = Path("src/codexbar/domain/settings.py")
BUDGET = Path("src/codexbar/application/budget.py")
CONTROLLER = Path("src/codexbar/ui/controller.py")
CONTROL_PANEL = Path("src/codexbar/ui/control_panel.py")
CONTROL_TRAY = Path("src/codexbar/ui/control_tray.py")
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


def _class_source(path: Path, class_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            segment = ast.get_source_segment(source, node)
            assert segment is not None
            return segment
    raise AssertionError(f"class {class_name} not found in {path}")


def _string_literals(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def test_inv_plan_001_core_has_no_history_or_context_authority_dependency() -> None:
    modules = _imported_modules(PLAN) | _imported_modules(PLAN_ALERTS)

    assert not any("history" in module for module in modules)
    assert not any(module.endswith(".context") for module in modules)


def test_inv_plan_002_and_003_core_has_no_persistence_or_concurrency_subsystem() -> None:
    modules = _imported_modules(PLAN) | _imported_modules(PLAN_ALERTS)
    source = PLAN.read_text(encoding="utf-8") + PLAN_ALERTS.read_text(encoding="utf-8")

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


def test_inv_plan_004_core_and_alerts_have_no_redeem_mutation_path() -> None:
    modules = _imported_modules(PLAN) | _imported_modules(PLAN_ALERTS)
    source = PLAN.read_text(encoding="utf-8") + PLAN_ALERTS.read_text(encoding="utf-8")

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
    literals = (
        _string_literals(PLAN)
        + _string_literals(PLAN_ALERTS)
        + _string_literals(SETTINGS)
    )
    source = (
        PLAN.read_text(encoding="utf-8")
        + PLAN_ALERTS.read_text(encoding="utf-8")
        + SETTINGS.read_text(encoding="utf-8")
    )

    assert not any("windowDurationMins" in literal for literal in literals)
    assert not any(literal.startswith("window_") for literal in literals)
    assert ".split(" not in source
    assert "parse_duration" not in source


def test_plan_uses_shared_neutral_quantities() -> None:
    plan_modules = _imported_modules(PLAN)
    alert_modules = _imported_modules(PLAN_ALERTS)
    settings_modules = _imported_modules(SETTINGS)

    assert "codexbar.domain.quantities" in plan_modules
    assert "codexbar.domain.quantities" in alert_modules
    assert "codexbar.domain.quantities" in settings_modules


def test_plan_panel_is_presentation_only_and_does_not_evaluate_policy() -> None:
    source = _class_source(CONTROL_PANEL, "PlanPanel")

    assert "evaluate_window_plan" not in source
    assert "AppSettings" not in source
    assert "BudgetRuntime" not in source
    assert "ResetOpportunityPolicy" not in source


def test_plan_alerts_use_existing_controller_snapshot_seam_without_second_polling_path() -> None:
    source = CONTROLLER.read_text(encoding="utf-8")

    assert source.count("self._plan_alert_service.process(") == 1
    assert "return self._state_from_snapshot(snapshot)" in source
    assert "plan_refresh" not in source
    assert "plan_timer" not in source


def test_post_redeem_current_adoption_stays_on_shared_controller_path() -> None:
    source = CONTROL_TRAY.read_text(encoding="utf-8")

    assert "self._controller.adopt_snapshot(observation.usage)" in source
    assert "PlanAlertService" not in source
    assert "evaluate_window_plan" not in source
