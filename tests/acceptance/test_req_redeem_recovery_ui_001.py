from pathlib import Path


def test_recovery_ui_reuses_attempt_id() -> None:
    panel_source = Path("src/codexbar/ui/control_panel.py").read_text()
    controller_source = Path("src/codexbar/application/redeem_execution.py").read_text()

    assert "Retry unresolved attempt" in panel_source
    assert "attempt_id: RedeemAttemptId = unresolved[0].attempt_id" in panel_source
    assert "controller.start_retry(attempt_id)" in panel_source
    assert "self._manager.retry(attempt_id)" in controller_source
