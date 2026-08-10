from pathlib import Path

from codexbar.ui.control_panel import BudgetPanel


def test_budget_panel_is_separate_presentation_surface() -> None:
    assert BudgetPanel.__name__ == "BudgetPanel"


def test_budget_panel_uses_user_facing_budget_language() -> None:
    source = Path("src/codexbar/ui/control_panel.py").read_text()

    assert "Remaining:" in source
    assert "Reserved:" in source
    assert "Available to use:" in source
    assert "Reset recommendation" in source
    assert "usable headroom" not in source
