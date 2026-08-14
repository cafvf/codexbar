from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowSample,
    HistoryInspection,
    HistoryInterval,
    HistoryState,
)
from codexbar.application.history_runtime import HistoryService
from codexbar.application.runtime_health import (
    RuntimeDiagnosticRegistry,
    RuntimeHealthSnapshotProvider,
    lineage_subsystem_health,
)
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
)
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import ResetCreditReadResult

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


class Reader:
    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        return AccountRateLimitsObservation(
            usage=UsageSnapshot(
                windows=(
                    UsageWindow(
                        UsageWindowId("dynamic"),
                        "Dynamic",
                        Fraction(Decimal("0.50")),
                    ),
                ),
                observed_at=NOW,
                source=UsageSource.MOCK,
            ),
            reset_credits=ResetCreditReadResult.unavailable("not relevant"),
        )


class Repo:
    def append(self, snapshot: HistoricalSnapshot) -> bool:
        return True

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        return ()

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]:
        return ()

    def prune(self, cutoff: datetime) -> int:
        return 0

    def inspect(self) -> HistoryInspection:
        return HistoryInspection("/tmp/test-history", HistoryState.READY_EMPTY)

    def clear(self) -> int:
        return 0


class ContextSource:
    def subsystem_health(self) -> SubsystemHealth:
        return SubsystemHealth(
            name="context",
            role=SubsystemRole.CONTEXT,
            availability=DiagnosticAvailability.AVAILABLE,
            operational_health=OperationalHealth.OK,
            evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
            summary="Context ready.",
            details=(DiagnosticDetail("revision_cache", True),),
        )


def _detail_map(subsystem: SubsystemHealth) -> dict[str, object]:
    return {detail.key: detail.value for detail in subsystem.details}


def test_task_762_runtime_health_exposes_revisions_cache_and_bounded_metrics() -> None:
    latest = LatestAccountObservationReader(Reader())
    observation = latest.read_account_rate_limits()
    history = HistoryService(Repo(), clock=lambda: NOW)
    history.process(observation.usage)
    metrics = RuntimeMetricCollector()
    metrics.record("context.ui_submit", 0.1)
    registry = RuntimeDiagnosticRegistry()
    registry.upsert(lineage_subsystem_health())

    snapshot = RuntimeHealthSnapshotProvider(
        latest,
        history,
        ContextSource(),
        metrics,
        registry,
        clock=lambda: NOW,
    ).snapshot()

    by_name = {item.name: item for item in snapshot.subsystems}
    assert _detail_map(by_name["current"])["current_revision"] == 1
    assert _detail_map(by_name["history"])["history_revision"] == 1
    assert _detail_map(by_name["context"])["revision_cache"] is True
    assert snapshot.runtime_metrics[0].operation == "context.ui_submit"
