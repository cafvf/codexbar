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
    RuntimeMetricSummary,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)
from codexbar.ui.system_health_panel import _summary_html, _technical_html
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class _Source:
    def __init__(self, *, metrics: tuple[RuntimeMetricSummary, ...] = ()) -> None:
        self._metrics = metrics

    def snapshot(self) -> SystemHealthSnapshot:
        return SystemHealthSnapshot(
            generated_at=NOW,
            subsystems=(
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
            runtime_metrics=self._metrics,
        )


def test_reset_monitoring_note_is_visible_once_in_default_summary() -> None:
    state = SystemHealthPresenter(_Source()).current()
    rendered = _summary_html(state)

    assert rendered.count("<b>Reset monitoring</b>") == 1
    assert "not enabled in v1.7" in rendered


def test_technical_details_render_actual_runtime_measurements_once() -> None:
    metric = RuntimeMetricSummary(
        operation="context.ui_poll",
        sample_count=20,
        failure_count=0,
        last_ms=0.031,
        p50_ms=0.020,
        p95_ms=0.047,
    )
    state = SystemHealthPresenter(_Source(metrics=(metric,))).current()
    rendered = _technical_html(state)

    assert rendered.count("Runtime measurements") == 1
    assert "Runtime performance" not in rendered
    assert "n=20" in rendered
    assert "last=0.031 ms" in rendered
    assert "p50=0.020 ms" in rendered
    assert "p95=0.047 ms" in rendered
    assert "built-in" not in rendered


def test_technical_details_explain_when_p95_has_too_few_samples() -> None:
    metric = RuntimeMetricSummary(
        operation="redeem.ui_submit",
        sample_count=3,
        failure_count=0,
        last_ms=0.050,
        p50_ms=0.040,
        p95_ms=None,
    )
    state = SystemHealthPresenter(_Source(metrics=(metric,))).current()
    rendered = _technical_html(state)

    assert "p50=0.040 ms" in rendered
    assert "p95=Not enough samples (needs 20)" in rendered
