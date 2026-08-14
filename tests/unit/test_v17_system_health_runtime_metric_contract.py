from __future__ import annotations

from datetime import UTC, datetime

from codexbar.domain.diagnostics import RuntimeMetricSummary, SystemHealthSnapshot
from codexbar.ui.system_health_viewmodel import (
    RuntimeMetricViewState,
    SystemHealthPresenter,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class _Source:
    def __init__(self, metric: RuntimeMetricSummary) -> None:
        self._metric = metric

    def snapshot(self) -> SystemHealthSnapshot:
        return SystemHealthSnapshot(
            generated_at=NOW,
            subsystems=(),
            runtime_metrics=(self._metric,),
        )


def test_presenter_owns_runtime_metric_formatting_contract() -> None:
    metric = RuntimeMetricSummary(
        operation="context.background",
        sample_count=20,
        failure_count=1,
        last_ms=18.125,
        p50_ms=17.628,
        p95_ms=22.433,
    )

    state = SystemHealthPresenter(_Source(metric)).current()
    presented = state.runtime_metrics[0]

    assert isinstance(presented, RuntimeMetricViewState)
    assert presented.operation == "context.background"
    assert presented.sample_count == 20
    assert presented.failure_count == 1
    assert presented.last == "18.125 ms"
    assert presented.p50 == "17.628 ms"
    assert presented.p95 == "22.433 ms"
    assert "n=20" in presented.summary
    assert "p50=17.628 ms" in presented.summary
    assert "p95=22.433 ms" in presented.summary
    assert "failures=1" in presented.summary


def test_presenter_never_interprets_callable_string_members_as_metric_values() -> None:
    metric = RuntimeMetricSummary(
        operation="redeem.ui_poll",
        sample_count=2,
        failure_count=0,
        last_ms=0.025,
        p50_ms=None,
        p95_ms=None,
    )

    presented = SystemHealthPresenter(_Source(metric)).current().runtime_metrics[0]

    assert presented.p50 == "Not enough samples (needs 3)"
    assert presented.p95 == "Not enough samples (needs 20)"
    assert "built-in" not in presented.summary
    assert "method" not in presented.summary
