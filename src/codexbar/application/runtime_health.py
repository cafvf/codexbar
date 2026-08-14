from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock
from typing import Protocol

from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.history_runtime import HistoryService
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    DiagnosticFreshness,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)
from codexbar.domain.models import Freshness


class ContextHealthSource(Protocol):
    def subsystem_health(self) -> SubsystemHealth: ...


class RuntimeDiagnosticRegistry:
    """Thread-safe live diagnostic facts supplied by runtime-owned UI integrations."""

    def __init__(self) -> None:
        self._items: dict[str, SubsystemHealth] = {}
        self._lock = RLock()

    def upsert(self, subsystem: SubsystemHealth) -> None:
        with self._lock:
            self._items[subsystem.name] = subsystem

    def snapshot(self) -> tuple[SubsystemHealth, ...]:
        with self._lock:
            return tuple(self._items[name] for name in sorted(self._items))


class RuntimeHealthSnapshotProvider:
    """Read-only live GUI health snapshot using the shared diagnostic domain model."""

    def __init__(
        self,
        latest_reader: LatestAccountObservationReader,
        history_service: HistoryService | None,
        context_source: ContextHealthSource,
        runtime_metrics: RuntimeMetricCollector,
        registry: RuntimeDiagnosticRegistry,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._latest_reader = latest_reader
        self._history_service = history_service
        self._context_source = context_source
        self._metrics = runtime_metrics
        self._registry = registry
        self._clock = clock or (lambda: datetime.now(UTC))

    def snapshot(self) -> SystemHealthSnapshot:
        generated_at = self._clock()
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("runtime health clock must be timezone-aware")

        dynamic = [
            *self._current_health(),
            self._history_health(),
            self._context_source.subsystem_health(),
            lineage_subsystem_health(),
            deferred_reset_monitor_health(),
        ]
        by_name = {item.name: item for item in dynamic}
        for item in self._registry.snapshot():
            by_name[item.name] = item
        return SystemHealthSnapshot(
            generated_at=generated_at.astimezone(UTC),
            subsystems=tuple(by_name[name] for name in sorted(by_name)),
            runtime_metrics=self._metrics.snapshot(),
        )

    def _current_health(self) -> tuple[SubsystemHealth, SubsystemHealth]:
        observation, revision = self._latest_reader.capture()
        if observation is None:
            return (
                SubsystemHealth(
                    name="codex_source",
                    role=SubsystemRole.SOURCE,
                    availability=DiagnosticAvailability.UNAVAILABLE,
                    operational_health=OperationalHealth.OK,
                    evidence_origin=EvidenceOrigin.UNAVAILABLE,
                    summary="Awaiting the first runtime Codex source observation.",
                ),
                SubsystemHealth(
                    name="current",
                    role=SubsystemRole.CURRENT,
                    availability=DiagnosticAvailability.UNAVAILABLE,
                    operational_health=OperationalHealth.OK,
                    evidence_origin=EvidenceOrigin.UNAVAILABLE,
                    summary="No runtime Current observation has been adopted yet.",
                    details=(DiagnosticDetail("current_revision", revision.value),),
                ),
            )

        usage = observation.usage
        stale = usage.freshness is Freshness.STALE
        freshness = DiagnosticFreshness.STALE if stale else DiagnosticFreshness.CURRENT
        return (
            SubsystemHealth(
                name="codex_source",
                role=SubsystemRole.SOURCE,
                availability=(
                    DiagnosticAvailability.UNAVAILABLE
                    if stale
                    else DiagnosticAvailability.AVAILABLE
                ),
                operational_health=(
                    OperationalHealth.DEGRADED if stale else OperationalHealth.OK
                ),
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                summary=(
                    "The latest source refresh failed; stale Current remains visible."
                    if stale
                    else "The latest runtime Codex source read succeeded."
                ),
            ),
            SubsystemHealth(
                name="current",
                role=SubsystemRole.CURRENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=(
                    OperationalHealth.DEGRADED if stale else OperationalHealth.OK
                ),
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                freshness=freshness,
                summary=(
                    "Current is stale after a failed refresh."
                    if stale
                    else "Authoritative Current usage is available."
                ),
                details=(
                    DiagnosticDetail("current_revision", revision.value),
                    DiagnosticDetail("window_count", len(usage.windows)),
                    DiagnosticDetail("observed_at", usage.observed_at.isoformat()),
                ),
            ),
        )

    def _history_health(self) -> SubsystemHealth:
        service = self._history_service
        if service is None:
            return SubsystemHealth(
                name="history",
                role=SubsystemRole.HISTORY,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=OperationalHealth.DEGRADED,
                evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
                summary="History runtime is unavailable in this GUI process.",
            )
        return SubsystemHealth(
            name="history",
            role=SubsystemRole.HISTORY,
            availability=DiagnosticAvailability.AVAILABLE,
            operational_health=OperationalHealth.OK,
            evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
            summary="History runtime is active.",
            details=(DiagnosticDetail("history_revision", service.revision.value),),
        )


def lineage_subsystem_health() -> SubsystemHealth:
    return SubsystemHealth(
        name="history_lineage",
        role=SubsystemRole.LINEAGE,
        availability=DiagnosticAvailability.AVAILABLE,
        operational_health=OperationalHealth.OK,
        evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
        summary=(
            "History/Context assume one local account. After intentionally switching "
            "ChatGPT accounts, clear local History before relying on cross-cycle Context."
        ),
        details=(
            DiagnosticDetail("mode", "single_account_assumption"),
            DiagnosticDetail("account_namespaced", False),
        ),
    )


def deferred_reset_monitor_health() -> SubsystemHealth:
    return SubsystemHealth(
        name="reset_monitor",
        role=SubsystemRole.DIAGNOSTICS,
        availability=DiagnosticAvailability.NOT_APPLICABLE,
        operational_health=OperationalHealth.OK,
        evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
        summary=(
            "Reset fact monitor primitives are deferred and inactive in v1.7; "
            "no expiry/count-change notifications are activated."
        ),
        details=(DiagnosticDetail("production_active", False),),
    )
