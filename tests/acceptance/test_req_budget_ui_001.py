from codexbar.ui.control_panel import BudgetPanel


def test_budget_panel_is_separate_presentation_surface() -> None:
    assert BudgetPanel.__name__ == "BudgetPanel"
