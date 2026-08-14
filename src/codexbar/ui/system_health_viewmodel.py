from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    DiagnosticFreshness,
    OperationalHealth,
    RuntimeMetricSummary,
    SubsystemHealth,
    SystemHealthSnapshot,
)


class SystemHealthSnapshotSource(Protocol):
    def snapshot(self) -> SystemHealthSnapshot: ...


@dataclass(frozen=True, slots=True)
class SystemHealthSubsystemViewState:
    name: str
    title: str
    role: str
    availability: str
    operational_health: str
    freshness: str
    status_label: str
    summary: str
    display_summary: str
    technical_details: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeMetricViewState:
    operation: str
    title: str
    sample_count: int
    failure_count: int
    last: str
    p50: str
    p95: str
    summary: str


@dataclass(frozen=True, slots=True)
class SystemHealthViewState:
    overall: str
    overall_label: str
    overall_summary: str
    generated_at: str
    subsystems: tuple[SystemHealthSubsystemViewState, ...]
    runtime_metrics: tuple[RuntimeMetricViewState, ...]


class SystemHealthPresenter:
    """Translate the shared health snapshot into a human-readable UI state."""

    def __init__(self, source: SystemHealthSnapshotSource) -> None:
        self._source = source

    def current(self) -> SystemHealthViewState:
        snapshot = self._source.snapshot()
        overall = snapshot.overall_health.value
        return SystemHealthViewState(
            overall=overall,
            overall_label=_overall_label(overall),
            overall_summary=_overall_summary(overall),
            generated_at=snapshot.generated_at.astimezone().isoformat(timespec="seconds"),
            subsystems=tuple(_subsystem_state(item) for item in snapshot.subsystems),
            runtime_metrics=tuple(_metric_state(item) for item in snapshot.runtime_metrics),
        )


def _subsystem_state(item: SubsystemHealth) -> SystemHealthSubsystemViewState:
    return SystemHealthSubsystemViewState(
        name=item.name,
        title=_subsystem_title(item.name),
        role=item.role.value,
        availability=item.availability.value,
        operational_health=item.operational_health.value,
        freshness=item.freshness.value,
        status_label=_status_label(item),
        summary=item.summary,
        display_summary=_display_summary(item),
        technical_details=tuple(_detail_text(detail) for detail in item.details),
    )


def _overall_label(value: str) -> str:
    return {
        "healthy": "Healthy",
        "degraded": "Degraded",
        "needs_attention": "Needs attention",
    }.get(value, value.replace("_", " ").title())


def _overall_summary(value: str) -> str:
    return {
        "healthy": "CodexBar's core runtime is operating normally.",
        "degraded": (
            "CodexBar is still usable, but one or more components are operating "
            "with reduced capability or stale information."
        ),
        "needs_attention": (
            "A core CodexBar component is unavailable or failed. Review the items "
            "marked as needing attention below."
        ),
    }.get(value, "Review the component status below.")


def _subsystem_title(name: str) -> str:
    return {
        "codex_source": "Codex connection",
        "current": "Current usage",
        "history": "Usage history",
        "context": "Historical Context",
        "history_lineage": "Account history scope",
        "reset_monitor": "Reset monitoring",
        "reset_ledger": "Reset ledger",
        "native_indicator": "Native tray indicator",
        "qt_fallback": "Qt tray fallback",
        "instance_ownership": "Application instance",
        "settings": "Settings",
        "environment": "Desktop environment",
        "diagnostics": "Diagnostics",
    }.get(name, name.replace("_", " ").title())


def _status_label(item: SubsystemHealth) -> str:
    if item.availability is DiagnosticAvailability.NOT_APPLICABLE:
        return "Standby" if item.name == "qt_fallback" else "Not enabled"
    if item.availability is DiagnosticAvailability.UNSUPPORTED:
        return "Unsupported"
    if item.operational_health is OperationalHealth.FAILED:
        return "Problem"
    if item.operational_health is OperationalHealth.DEGRADED:
        return "Degraded"
    if item.availability is DiagnosticAvailability.UNAVAILABLE:
        return "Unavailable"
    if item.freshness is DiagnosticFreshness.STALE:
        return "Stale"
    return "Healthy"


def _display_summary(item: SubsystemHealth) -> str:
    handler = {
        "codex_source": _source_summary,
        "current": _current_summary,
        "history": _history_summary,
        "context": _context_summary,
        "history_lineage": _lineage_summary,
        "reset_monitor": _reset_monitor_summary,
        "native_indicator": _native_indicator_summary,
        "qt_fallback": _qt_fallback_summary,
        "instance_ownership": _instance_ownership_summary,
    }.get(item.name)
    return item.summary if handler is None else handler(item)


def _source_summary(item: SubsystemHealth) -> str:
    if item.availability is DiagnosticAvailability.AVAILABLE:
        return "Codex is responding to usage refresh requests."
    return "The latest Codex refresh is unavailable; previous data may remain visible."


def _current_summary(item: SubsystemHealth) -> str:
    if item.freshness is DiagnosticFreshness.STALE:
        return "Current usage is showing the last known values after a failed refresh."
    if item.availability is DiagnosticAvailability.AVAILABLE:
        return "Current usage data is available and can be shown in the tray and details."
    return "No current usage observation has been adopted yet."


def _history_summary(item: SubsystemHealth) -> str:
    if item.availability is DiagnosticAvailability.AVAILABLE:
        return "Local usage history is available for charts and historical comparisons."
    return "Local usage history is currently unavailable."


def _context_summary(item: SubsystemHealth) -> str:
    phase = _detail_value(item.details, "phase")
    if item.operational_health is OperationalHealth.DEGRADED:
        return "Historical Context encountered an unexpected runtime error."
    if phase == "idle":
        return (
            "Historical Context is ready. Open Usage history to calculate the "
            "current historical comparison."
        )
    if phase == "loading":
        return "Historical Context is updating in the background."
    if phase == "ready":
        return "Historical Context is ready and uses revision-aware cached data when valid."
    if item.availability is DiagnosticAvailability.UNAVAILABLE:
        return "Historical Context is not currently available."
    return "Historical Context is available."


def _lineage_summary(_item: SubsystemHealth) -> str:
    return (
        "CodexBar stores History and Historical Context for one local ChatGPT account "
        "at a time. If you intentionally switch accounts, clear History first so "
        "observations from different accounts are not mixed."
    )


def _reset_monitor_summary(_item: SubsystemHealth) -> str:
    return (
        "Automatic monitoring for reset-count or reset-expiry changes is not enabled "
        "in v1.7. CodexBar will not generate notifications from that deferred monitor."
    )


def _native_indicator_summary(item: SubsystemHealth) -> str:
    if item.availability is DiagnosticAvailability.AVAILABLE:
        return "The Ubuntu/Ayatana tray integration is active."
    return "The native tray integration is unavailable; CodexBar can use the Qt fallback."


def _qt_fallback_summary(item: SubsystemHealth) -> str:
    if item.availability is DiagnosticAvailability.AVAILABLE:
        return "The Qt tray fallback is currently active."
    return "The Qt tray fallback is ready but not needed while the native tray is healthy."


def _instance_ownership_summary(item: SubsystemHealth) -> str:
    if item.operational_health is OperationalHealth.FAILED:
        return "CodexBar could not establish a healthy single-instance owner."
    return "One CodexBar GUI instance owns this desktop session."


def _detail_value(details: tuple[DiagnosticDetail, ...], key: str) -> object | None:
    for detail in details:
        if detail.key == key:
            return detail.value
    return None


def _detail_text(detail: DiagnosticDetail) -> str:
    label = {
        "current_revision": "Current data revision",
        "history_revision": "History revision",
        "window_count": "Usage windows",
        "observed_at": "Observed at",
        "phase": "Worker state",
        "generation": "Request generation",
        "busy": "Background work active",
        "revision_cache": "Revision-aware cache",
        "stderr_line_count": "Recent helper stderr lines",
        "mode": "Storage mode",
        "account_namespaced": "History separated by account",
        "production_active": "Enabled in production",
    }.get(detail.key, detail.key.replace("_", " ").title())
    return f"{label}: {_display_scalar(detail.value)}"


def _display_scalar(value: object) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    if value is None:
        return "Not available"
    return str(value)


def _metric_state(metric: RuntimeMetricSummary) -> RuntimeMetricViewState:
    title = _metric_title(metric.operation)
    last = _duration_text(metric.last_ms)
    p50 = _quantile_text(metric.p50_ms, metric.sample_count, minimum_samples=3)
    p95 = _quantile_text(metric.p95_ms, metric.sample_count, minimum_samples=20)
    parts = [
        f"{title}: n={metric.sample_count}",
        f"last={last}",
        f"p50={p50}",
        f"p95={p95}",
    ]
    if metric.failure_count:
        parts.append(f"failures={metric.failure_count}")
    return RuntimeMetricViewState(
        operation=metric.operation,
        title=title,
        sample_count=metric.sample_count,
        failure_count=metric.failure_count,
        last=last,
        p50=p50,
        p95=p95,
        summary=" · ".join(parts),
    )


def _metric_title(operation: str) -> str:
    return {
        "context.ui_submit": "Historical Context UI submission",
        "context.ui_poll": "Historical Context UI polling",
        "context.background": "Historical Context background calculation",
        "redeem.ui_submit": "Redeem UI submission",
        "redeem.ui_poll": "Redeem UI polling",
        "redeem.background": "Redeem background operation",
    }.get(operation, operation.replace("_", " "))


def _duration_text(value: float | None) -> str:
    return "Not available" if value is None else f"{value:.3f} ms"


def _quantile_text(
    value: float | None,
    sample_count: int,
    *,
    minimum_samples: int,
) -> str:
    if value is not None:
        return f"{value:.3f} ms"
    if sample_count < minimum_samples:
        return f"Not enough samples (needs {minimum_samples})"
    return "Not available"
