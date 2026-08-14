from __future__ import annotations

from pathlib import Path

from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.diagnostics import DiagnosticAvailability, OperationalHealth
from codexbar.ui.context_controller import ContextController


class _IdleContextSource:
    def capture_request(self):
        return None

    def current_identity(self):
        return CurrentRevision(4), HistoryRevision(7)

    def evaluate_request(self, request):
        raise AssertionError("idle health must not evaluate Context")


def test_context_health_is_ready_not_unavailable_before_first_evaluation() -> None:
    controller = ContextController(_IdleContextSource())
    try:
        health = controller.subsystem_health()
    finally:
        controller.close()

    assert health.availability is DiagnosticAvailability.AVAILABLE
    assert health.operational_health is OperationalHealth.OK
    assert "not been evaluated" in health.summary
    details = {detail.key: detail.value for detail in health.details}
    assert details["phase"] == "idle"
    assert details["current_revision"] == 4
    assert details["history_revision"] == 7


def test_system_health_dialog_refreshes_live_while_visible() -> None:
    source = Path("src/codexbar/ui/system_health_panel.py").read_text(encoding="utf-8")

    assert "QTimer" in source
    assert "self._refresh_timer.setInterval(750)" in source
    assert "self._refresh_timer.timeout.connect(self.refresh)" in source
    assert "def showEvent" in source
    assert "self._refresh_timer.start()" in source
    assert "def hideEvent" in source
    assert "self._refresh_timer.stop()" in source


def test_historical_context_idle_copy_is_user_facing() -> None:
    source = Path("src/codexbar/ui/system_health_viewmodel.py").read_text(
        encoding="utf-8"
    )

    assert 'if phase == "idle":' in source
    assert "Open Usage history to calculate" in source
