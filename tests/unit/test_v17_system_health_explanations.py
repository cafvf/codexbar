from __future__ import annotations

from datetime import UTC, datetime

from codexbar.application.revisions import CurrentRevision
from codexbar.application.runtime_health import (
    RuntimeDiagnosticRegistry,
    RuntimeHealthSnapshotProvider,
    deferred_reset_monitor_health,
    lineage_subsystem_health,
)
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)
from codexbar.ui.system_health_panel import _summary_html, _technical_html
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class _Latest:
    def capture(self):
        return None, CurrentRevision()


class _Context:
    def subsystem_health(self) -> SubsystemHealth:
        return SubsystemHealth(
            name="context",
            role=SubsystemRole.CONTEXT,
            availability=DiagnosticAvailability.AVAILABLE,
            operational_health=OperationalHealth.OK,
            evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
            summary="Context has not been evaluated.",
        )


class _Source:
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


def test_runtime_health_always_contains_deferred_product_notes() -> None:
    provider = RuntimeHealthSnapshotProvider(
        _Latest(),
        None,
        _Context(),
        RuntimeMetricCollector(),
        RuntimeDiagnosticRegistry(),
        clock=lambda: NOW,
    )

    names = {item.name for item in provider.snapshot().subsystems}

    assert "reset_monitor" in names
    assert "history_lineage" in names


def test_system_health_puts_important_notes_before_components() -> None:
    state = SystemHealthPresenter(_Source()).current()
    rendered = _summary_html(state)

    assert rendered.index("Important notes") < rendered.index("Components")


def test_technical_details_explain_revision_and_quantiles() -> None:
    state = SystemHealthPresenter(_Source()).current()
    rendered = _technical_html(state)

    assert "How to read these details" in rendered
    assert "<b>Revision</b>" in rendered
    assert "internal version counter" in rendered
    assert "<b>p95</b>" in rendered
    assert "95th-percentile duration" in rendered
    assert "<b>p50 / median</b>" in rendered
