from __future__ import annotations

from datetime import UTC, datetime

from codexbar.application.runtime_health import (
    deferred_reset_monitor_health,
    lineage_subsystem_health,
)
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    EvidenceOrigin,
    OperationalHealth,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class Source:
    def snapshot(self) -> SystemHealthSnapshot:
        return SystemHealthSnapshot(
            NOW,
            (
                SubsystemHealth(
                    name="current",
                    role=SubsystemRole.CURRENT,
                    availability=DiagnosticAvailability.AVAILABLE,
                    operational_health=OperationalHealth.OK,
                    evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                    summary="Current healthy.",
                ),
            ),
        )


def test_task_760_ui_view_state_is_derived_from_shared_health_snapshot() -> None:
    state = SystemHealthPresenter(Source()).current()
    assert state.overall == "healthy"
    assert state.subsystems[0].name == "current"
    assert state.subsystems[0].summary == "Current healthy."


def test_task_763_lineage_wording_is_explicit_and_actionable() -> None:
    lineage = lineage_subsystem_health()
    assert lineage.role is SubsystemRole.LINEAGE
    assert "one local account" in lineage.summary
    assert "clear local History" in lineage.summary


def test_task_767_reset_monitor_is_explicitly_deferred_and_inactive() -> None:
    monitor = deferred_reset_monitor_health()
    assert monitor.availability is DiagnosticAvailability.NOT_APPLICABLE
    assert "deferred and inactive" in monitor.summary
    assert monitor.details[0].value is False
