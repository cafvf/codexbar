from pathlib import Path


def test_redeem_button_requires_positive_available_reset_count() -> None:
    source = Path("src/codexbar/ui/control_panel.py").read_text()

    assert "has_available_credit" in source
    assert "state.reset.available_count > 0" in source
    assert "and has_available_credit" in source
    assert "No reset credits available." in source
