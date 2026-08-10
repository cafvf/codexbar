from pathlib import Path


def test_usage_reserve_is_part_of_canonical_app_settings() -> None:
    domain = Path("src/codexbar/domain/settings.py").read_text()
    infrastructure = Path("src/codexbar/infrastructure/settings.py").read_text()

    assert "usage_reserves" in domain
    assert '"usage_reserves"' in infrastructure


def test_no_control_policy_sidecar_is_introduced() -> None:
    names = {
        path.name
        for path in Path("src/codexbar/infrastructure").glob("*.py")
    }
    assert "control_settings.py" not in names
    assert "budget_settings.py" not in names
    assert "reserve_settings.py" not in names


def test_budget_core_has_no_history_ledger_or_infrastructure_dependency() -> None:
    source = Path("src/codexbar/application/budget.py").read_text()

    assert "history" not in source
    assert "reset_ledger" not in source
    assert "codexbar.infrastructure" not in source
