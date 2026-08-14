from pathlib import Path


def test_redeem_requires_explicit_confirmation_and_mentions_backend_choice() -> None:
    source = Path("src/codexbar/ui/control_panel.py").read_text()
    assert "QMessageBox.question" in source
    assert "backend will choose the credit" in source
    assert "controller.busy" in source
    assert "controller.start_redeem" in source
