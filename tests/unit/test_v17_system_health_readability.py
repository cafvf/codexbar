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
                lineage_subsystem_health(),
                deferred_reset_monitor_health(),
            ),
        )


def test_phase_f_health_presentation_uses_human_readable_labels() -> None:
    state = SystemHealthPresenter(Source()).current()
    by_name = {item.name: item for item in state.subsystems}

    assert state.overall_label == "Healthy"
    assert "operating normally" in state.overall_summary
    assert by_name["current"].title == "Current usage"
    assert by_name["current"].status_label == "Healthy"
    assert "Current usage data is available" in by_name["current"].display_summary


def test_phase_f_lineage_and_reset_monitor_are_explained_in_plain_language() -> None:
    state = SystemHealthPresenter(Source()).current()
    by_name = {item.name: item for item in state.subsystems}

    lineage = by_name["history_lineage"].display_summary
    assert "one local ChatGPT account at a time" in lineage
    assert "clear History first" in lineage

    reset = by_name["reset_monitor"]
    assert reset.status_label == "Not enabled"
    assert "not enabled in v1.7" in reset.display_summary
