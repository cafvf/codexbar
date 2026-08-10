from pathlib import Path


def test_recovery_ui_reuses_attempt_id() -> None:
    source = Path("src/codexbar/ui/control_panel.py").read_text()

    assert "Retry unresolved attempt" in source
    assert "attempt_id: RedeemAttemptId = unresolved[0].attempt_id" in source
    assert "manager.retry(attempt_id)" in source
