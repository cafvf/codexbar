from __future__ import annotations

from datetime import UTC, datetime

from codexbar.domain.diagnostics import RuntimeMetricSummary, SystemHealthSnapshot
from codexbar.ui.system_health_panel import _technical_html
from codexbar.ui.system_health_viewmodel import SystemHealthPresenter

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class _Source:
    def __init__(self, metrics: tuple[RuntimeMetricSummary, ...]) -> None:
        self._metrics = metrics

    def snapshot(self) -> SystemHealthSnapshot:
        return SystemHealthSnapshot(
            generated_at=NOW,
            subsystems=(),
            runtime_metrics=self._metrics,
        )


def test_runtime_metric_html_is_escaped_and_contains_presented_values() -> None:
    metric = RuntimeMetricSummary(
        operation="<unsafe>",
        sample_count=20,
        failure_count=0,
        last_ms=0.031,
        p50_ms=0.020,
        p95_ms=0.047,
    )

    rendered = _technical_html(
        SystemHealthPresenter(_Source((metric,))).current()
    )

    assert "&lt;unsafe&gt;" in rendered
    assert "<unsafe>" not in rendered
    assert "n=20" in rendered
    assert "p50=0.020 ms" in rendered
    assert "p95=0.047 ms" in rendered


def test_runtime_metric_empty_state_is_explicit() -> None:
    rendered = _technical_html(
        SystemHealthPresenter(_Source(())).current()
    )

    assert "No runtime measurement samples have been retained yet" in rendered
