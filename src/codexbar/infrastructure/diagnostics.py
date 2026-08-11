from __future__ import annotations

import importlib.util
import platform
from dataclasses import dataclass
from pathlib import Path

from codexbar import __version__
from codexbar.application.account import AccountRateLimitsReader
from codexbar.application.diagnostics import (
    DiagnosticProvider,
    DiagnosticService,
    sanitize_diagnostic_text,
)
from codexbar.application.history import HistoryState
from codexbar.application.reset_ledger import ResetLedgerState
from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    DiagnosticFreshness,
    EvidenceOrigin,
    OperationalHealth,
    RuntimeMetricCollector,
    SubsystemHealth,
    SubsystemRole,
)
from codexbar.domain.errors import CodexBarError
from codexbar.domain.models import Freshness
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
from codexbar.infrastructure.settings import JsonSettingsRepository


@dataclass(frozen=True, slots=True)
class HistoryDiagnosticProvider(DiagnosticProvider):
    path: Path

    @property
    def metric_key(self) -> str:
        return "diagnostics.history"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        inspection = SqliteHistoryRepository.inspect_path(self.path)
        if inspection.state in {HistoryState.UNREADABLE, HistoryState.UNSUPPORTED}:
            availability = (
                DiagnosticAvailability.UNSUPPORTED
                if inspection.state is HistoryState.UNSUPPORTED
                else DiagnosticAvailability.UNAVAILABLE
            )
            health = OperationalHealth.FAILED
        else:
            availability = DiagnosticAvailability.AVAILABLE
            health = OperationalHealth.OK

        details = [DiagnosticDetail("state", inspection.state.value)]
        if inspection.schema_version is not None:
            details.append(DiagnosticDetail("schema_version", inspection.schema_version))
        if inspection.snapshot_count is not None:
            details.append(DiagnosticDetail("snapshot_count", inspection.snapshot_count))
        if inspection.oldest_observed_at is not None:
            details.append(
                DiagnosticDetail("oldest_observed_at", inspection.oldest_observed_at.isoformat())
            )
        if inspection.newest_observed_at is not None:
            details.append(
                DiagnosticDetail("newest_observed_at", inspection.newest_observed_at.isoformat())
            )

        summary = inspection.diagnostic or f"History state is {inspection.state.value}."
        return (
            SubsystemHealth(
                name="history",
                role=SubsystemRole.HISTORY,
                availability=availability,
                operational_health=health,
                evidence_origin=EvidenceOrigin.LOCAL_PERSISTED_INSPECTION,
                summary=sanitize_diagnostic_text(summary),
                details=tuple(details),
            ),
        )


@dataclass(frozen=True, slots=True)
class ResetLedgerDiagnosticProvider(DiagnosticProvider):
    path: Path

    @property
    def metric_key(self) -> str:
        return "diagnostics.reset_ledger"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        inspection = SqliteResetEventRepository.inspect_path(self.path)
        if inspection.state in {ResetLedgerState.UNREADABLE, ResetLedgerState.UNSUPPORTED}:
            availability = (
                DiagnosticAvailability.UNSUPPORTED
                if inspection.state is ResetLedgerState.UNSUPPORTED
                else DiagnosticAvailability.UNAVAILABLE
            )
            health = OperationalHealth.FAILED
        else:
            availability = DiagnosticAvailability.AVAILABLE
            health = OperationalHealth.OK

        details = [DiagnosticDetail("state", inspection.state.value)]
        if inspection.schema_version is not None:
            details.append(DiagnosticDetail("schema_version", inspection.schema_version))
        if inspection.event_count is not None:
            details.append(DiagnosticDetail("event_count", inspection.event_count))
        if inspection.unresolved_attempt_count is not None:
            details.append(
                DiagnosticDetail("unresolved_attempt_count", inspection.unresolved_attempt_count)
            )
        return (
            SubsystemHealth(
                name="reset_ledger",
                role=SubsystemRole.RESET_LEDGER,
                availability=availability,
                operational_health=health,
                evidence_origin=EvidenceOrigin.LOCAL_PERSISTED_INSPECTION,
                summary=f"Reset ledger state is {inspection.state.value}.",
                details=tuple(details),
            ),
        )


@dataclass(frozen=True, slots=True)
class SettingsDiagnosticProvider(DiagnosticProvider):
    repository: JsonSettingsRepository

    @property
    def metric_key(self) -> str:
        return "diagnostics.settings"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        result = self.repository.load()
        health = (
            OperationalHealth.DEGRADED
            if result.diagnostic is not None
            else OperationalHealth.OK
        )
        details = [DiagnosticDetail("origin", result.origin.value)]
        if result.source_schema_version is not None:
            details.append(DiagnosticDetail("schema_version", result.source_schema_version))
        summary = (
            sanitize_diagnostic_text(str(result.diagnostic))
            if result.diagnostic is not None
            else f"Settings loaded from {result.origin.value}."
        )
        return (
            SubsystemHealth(
                name="settings",
                role=SubsystemRole.SETTINGS,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=health,
                evidence_origin=EvidenceOrigin.LOCAL_PERSISTED_INSPECTION,
                summary=summary,
                details=tuple(details),
            ),
        )


@dataclass(frozen=True, slots=True)
class CurrentSourceDiagnosticProvider(DiagnosticProvider):
    reader: AccountRateLimitsReader

    @property
    def metric_key(self) -> str:
        return "diagnostics.source_probe"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        try:
            observation = self.reader.read_account_rate_limits()
        except (CodexBarError, ValueError) as exc:
            detail = sanitize_diagnostic_text(str(exc))
            return (
                SubsystemHealth(
                    name="codex_source",
                    role=SubsystemRole.SOURCE,
                    availability=DiagnosticAvailability.UNAVAILABLE,
                    operational_health=OperationalHealth.FAILED,
                    evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                    summary=f"Read-only Codex source probe failed: {detail}",
                ),
                SubsystemHealth(
                    name="current",
                    role=SubsystemRole.CURRENT,
                    availability=DiagnosticAvailability.UNAVAILABLE,
                    operational_health=OperationalHealth.FAILED,
                    evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                    summary="No usable Current observation was produced by the fresh source probe.",
                ),
            )

        usage = observation.usage
        freshness = (
            DiagnosticFreshness.CURRENT
            if usage.freshness is Freshness.CURRENT
            else DiagnosticFreshness.STALE
        )
        return (
            SubsystemHealth(
                name="codex_source",
                role=SubsystemRole.SOURCE,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                summary="Codex app-server rate-limit read succeeded.",
            ),
            SubsystemHealth(
                name="current",
                role=SubsystemRole.CURRENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                freshness=freshness,
                summary="Fresh Current usage evidence is available.",
                details=(
                    DiagnosticDetail("observed_at", usage.observed_at.isoformat()),
                    DiagnosticDetail("window_count", len(usage.windows)),
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class UnprobedCurrentSourceDiagnosticProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.source_unprobed"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        return (
            SubsystemHealth(
                name="codex_source",
                role=SubsystemRole.SOURCE,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.UNAVAILABLE,
                summary=(
                    "External source probe was intentionally omitted from this "
                    "local-only snapshot."
                ),
            ),
            SubsystemHealth(
                name="current",
                role=SubsystemRole.CURRENT,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.UNAVAILABLE,
                summary="Live Current evidence is unavailable in this local-only snapshot.",
            ),
        )


@dataclass(frozen=True, slots=True)
class ContextDiagnosticProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.context"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        return (
            SubsystemHealth(
                name="context",
                role=SubsystemRole.CONTEXT,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.UNAVAILABLE,
                summary="Live Context runtime evidence is unavailable outside the GUI process.",
                details=(
                    DiagnosticDetail("coverage", "unavailable"),
                    DiagnosticDetail("account_namespaced", False),
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class LineageDiagnosticProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.lineage"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        return (
            SubsystemHealth(
                name="history_lineage",
                role=SubsystemRole.LINEAGE,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.LOCAL_PERSISTED_INSPECTION,
                summary=(
                    "History/Context use a single-account local-history assumption; "
                    "no supported stable account identifier namespaces persisted history."
                ),
                details=(
                    DiagnosticDetail("mode", "single_account_assumption"),
                    DiagnosticDetail("account_namespaced", False),
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class DesktopBackendDiagnosticProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.desktop_backends"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        qt_available = importlib.util.find_spec("PySide6") is not None
        return (
            SubsystemHealth(
                name="native_indicator",
                role=SubsystemRole.NATIVE_INDICATOR,
                availability=DiagnosticAvailability.UNAVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.UNAVAILABLE,
                summary="Live native-indicator backend state is available only in the GUI runtime.",
            ),
            SubsystemHealth(
                name="qt_fallback",
                role=SubsystemRole.QT_FALLBACK,
                availability=(
                    DiagnosticAvailability.AVAILABLE
                    if qt_available
                    else DiagnosticAvailability.UNSUPPORTED
                ),
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                summary=(
                    "PySide6 is import-discoverable for the Qt fallback."
                    if qt_available
                    else "PySide6 is not installed in this execution environment."
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentDiagnosticProvider(DiagnosticProvider):
    @property
    def metric_key(self) -> str:
        return "diagnostics.environment"

    def collect(self) -> tuple[SubsystemHealth, ...]:
        return (
            SubsystemHealth(
                name="runtime_environment",
                role=SubsystemRole.ENVIRONMENT,
                availability=DiagnosticAvailability.AVAILABLE,
                operational_health=OperationalHealth.OK,
                evidence_origin=EvidenceOrigin.FRESH_READ_ONLY_PROBE,
                summary=(
                    "Local runtime metadata collected without reading private "
                    "authentication state."
                ),
                details=(
                    DiagnosticDetail("codexbar_version", __version__),
                    DiagnosticDetail("python_version", platform.python_version()),
                    DiagnosticDetail("platform", platform.system()),
                    DiagnosticDetail("platform_release", platform.release()),
                ),
            ),
        )


def build_doctor_service(
    *,
    include_source_probe: bool = True,
    source_reader: AccountRateLimitsReader | None = None,
    runtime_metrics: RuntimeMetricCollector | None = None,
) -> DiagnosticService:
    providers: list[DiagnosticProvider] = [
        EnvironmentDiagnosticProvider(),
        SettingsDiagnosticProvider(JsonSettingsRepository()),
        HistoryDiagnosticProvider(history_database_path()),
        ResetLedgerDiagnosticProvider(reset_ledger_database_path()),
        LineageDiagnosticProvider(),
        ContextDiagnosticProvider(),
        DesktopBackendDiagnosticProvider(),
    ]
    if include_source_probe:
        providers.append(
            CurrentSourceDiagnosticProvider(source_reader or CodexAccountRateLimitsReader())
        )
    else:
        providers.append(UnprobedCurrentSourceDiagnosticProvider())
    return DiagnosticService(
        providers=tuple(providers),
        runtime_metrics=runtime_metrics or RuntimeMetricCollector(),
    )
