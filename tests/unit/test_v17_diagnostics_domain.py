from datetime import UTC, datetime

import pytest

from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    DiagnosticFreshness,
    EvidenceOrigin,
    OperationalHealth,
    OverallHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


def health(
    name: str,
    role: SubsystemRole,
    *,
    availability: DiagnosticAvailability = DiagnosticAvailability.AVAILABLE,
    operational: OperationalHealth = OperationalHealth.OK,
    freshness: DiagnosticFreshness = DiagnosticFreshness.UNKNOWN,
    details: tuple[DiagnosticDetail, ...] = (),
) -> SubsystemHealth:
    return SubsystemHealth(
        name=name,
        role=role,
        availability=availability,
        operational_health=operational,
        evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
        freshness=freshness,
        summary=f"{name} diagnostic",
        details=details,
    )


def snapshot(*subsystems: SubsystemHealth) -> SystemHealthSnapshot:
    return SystemHealthSnapshot(generated_at=NOW, subsystems=tuple(subsystems))


def test_tv_1701_context_insufficient_and_native_unavailable_with_qt_fallback_is_healthy() -> None:
    value = snapshot(
        health("source", SubsystemRole.SOURCE),
        health("current", SubsystemRole.CURRENT, freshness=DiagnosticFreshness.CURRENT),
        health("history", SubsystemRole.HISTORY),
        health(
            "context",
            SubsystemRole.CONTEXT,
            details=(DiagnosticDetail("coverage", "insufficient"), DiagnosticDetail("n", 0)),
        ),
        health(
            "native",
            SubsystemRole.NATIVE_INDICATOR,
            availability=DiagnosticAvailability.UNAVAILABLE,
        ),
        health("qt", SubsystemRole.QT_FALLBACK),
    )

    assert value.overall_health is OverallHealth.HEALTHY


def test_tv_1702_stale_current_degrades_without_failing_history() -> None:
    value = snapshot(
        health("source", SubsystemRole.SOURCE),
        health("current", SubsystemRole.CURRENT, freshness=DiagnosticFreshness.STALE),
        health("history", SubsystemRole.HISTORY),
    )

    assert value.overall_health is OverallHealth.DEGRADED


def test_tv_1703_no_usable_current_and_failed_source_needs_attention() -> None:
    value = snapshot(
        health(
            "source",
            SubsystemRole.SOURCE,
            availability=DiagnosticAvailability.UNAVAILABLE,
            operational=OperationalHealth.FAILED,
        ),
        health(
            "current",
            SubsystemRole.CURRENT,
            availability=DiagnosticAvailability.UNAVAILABLE,
            operational=OperationalHealth.FAILED,
        ),
    )

    assert value.overall_health is OverallHealth.NEEDS_ATTENTION


def test_optional_unsupported_capability_is_factual_not_failed() -> None:
    value = snapshot(
        health("source", SubsystemRole.SOURCE),
        health("current", SubsystemRole.CURRENT, freshness=DiagnosticFreshness.CURRENT),
        health(
            "native",
            SubsystemRole.NATIVE_INDICATOR,
            availability=DiagnosticAvailability.UNSUPPORTED,
        ),
    )

    assert value.overall_health is OverallHealth.HEALTHY


def test_noncritical_operational_failure_degrades() -> None:
    value = snapshot(
        health("source", SubsystemRole.SOURCE),
        health("current", SubsystemRole.CURRENT, freshness=DiagnosticFreshness.CURRENT),
        health("history", SubsystemRole.HISTORY, operational=OperationalHealth.FAILED),
    )

    assert value.overall_health is OverallHealth.DEGRADED


def test_failed_instance_ownership_invariant_needs_attention() -> None:
    value = snapshot(
        health("source", SubsystemRole.SOURCE),
        health("current", SubsystemRole.CURRENT, freshness=DiagnosticFreshness.CURRENT),
        health(
            "instance",
            SubsystemRole.INSTANCE_OWNERSHIP,
            operational=OperationalHealth.FAILED,
        ),
    )

    assert value.overall_health is OverallHealth.NEEDS_ATTENTION


def test_tv_1704_metric_thresholds_and_capacity_are_exact() -> None:
    collector = RuntimeMetricCollector()

    collector.record("context", 1.0)
    summary = collector.summary("context")
    assert summary.sample_count == 1
    assert summary.last_ms == 1.0
    assert summary.p50_ms is None
    assert summary.p95_ms is None

    collector.record("context", 2.0)
    assert collector.summary("context").p50_ms is None

    collector.record("context", 3.0)
    assert collector.summary("context").p50_ms == 2.0

    for duration in range(4, 20):
        collector.record("context", float(duration))
    assert collector.summary("context").p95_ms is None

    collector.record("context", 20.0)
    assert collector.summary("context").p95_ms == pytest.approx(19.05)

    for duration in range(21, 66):
        collector.record("context", float(duration))

    retained = collector.retained_samples("context")
    assert len(retained) == 64
    assert [sample.duration_ms for sample in retained] == [float(value) for value in range(2, 66)]


def test_runtime_metric_measurement_uses_injected_monotonic_clock() -> None:
    ticks = iter((10.0, 10.125))
    collector = RuntimeMetricCollector(monotonic=lambda: next(ticks))

    with collector.measure("doctor.local"):
        pass

    assert collector.summary("doctor.local").last_ms == pytest.approx(125.0)


def test_runtime_metric_rejects_backward_monotonic_clock() -> None:
    ticks = iter((10.0, 9.0))
    collector = RuntimeMetricCollector(monotonic=lambda: next(ticks))

    with pytest.raises(ValueError, match="backwards"), collector.measure("doctor.local"):
        pass
