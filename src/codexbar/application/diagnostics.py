from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from codexbar.domain.diagnostics import (
    DiagnosticDetail,
    RuntimeMetricCollector,
    RuntimeMetricSummary,
    SubsystemHealth,
    SubsystemRole,
    SystemHealthSnapshot,
)

DIAGNOSTICS_SCHEMA_VERSION = 1

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_JWT_RE = re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_OPENAI_TOKEN_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(access[_-]?token|refresh[_-]?token|token|secret|credential|password)"
    r"\b[\"']?\s*[:=]\s*[\"']?[^\"',;\s}\]]+[\"']?"
)
_SENSITIVE_DETAIL_MARKERS = (
    "email",
    "token",
    "jwt",
    "secret",
    "credential",
    "password",
    "auth_payload",
)


class DiagnosticProvider(Protocol):
    @property
    def metric_key(self) -> str: ...

    def collect(self) -> tuple[SubsystemHealth, ...]: ...


@dataclass(slots=True)
class DiagnosticService:
    providers: Sequence[DiagnosticProvider]
    runtime_metrics: RuntimeMetricCollector
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def collect(self) -> SystemHealthSnapshot:
        subsystems: list[SubsystemHealth] = []
        for provider in self.providers:
            with self.runtime_metrics.measure(provider.metric_key):
                subsystems.extend(provider.collect())

        generated_at = self.clock()
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("diagnostic clock must return a timezone-aware datetime")
        return SystemHealthSnapshot(
            generated_at=generated_at,
            subsystems=tuple(subsystems),
            runtime_metrics=self.runtime_metrics.snapshot(),
        )


def render_doctor_text(snapshot: SystemHealthSnapshot) -> str:
    lines = [
        "CodexBar Doctor",
        f"Overall: {snapshot.overall_health.value}",
        f"Generated: {snapshot.generated_at.isoformat()}",
        "",
        "Subsystems:",
    ]
    for subsystem in snapshot.subsystems:
        freshness = (
            ""
            if subsystem.freshness.value == "unknown"
            else f", freshness={subsystem.freshness.value}"
        )
        lines.append(
            f"- {subsystem.name}: availability={subsystem.availability.value}, "
            f"health={subsystem.operational_health.value}{freshness}, "
            f"evidence={subsystem.evidence_origin.value}"
        )
        lines.append(f"  {sanitize_diagnostic_text(subsystem.summary)}")
        for detail in _safe_details(subsystem.details):
            lines.append(f"  {detail.key}: {detail.value}")

    if snapshot.runtime_metrics:
        lines.extend(("", "Runtime metrics:"))
        for metric in snapshot.runtime_metrics:
            lines.append(_metric_text(metric))
    return "\n".join(lines)


def doctor_json_document(snapshot: SystemHealthSnapshot) -> dict[str, object]:
    return {
        "diagnostics_schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "generated_at": snapshot.generated_at.isoformat(),
        "overall_health": snapshot.overall_health.value,
        "subsystems": [
            {
                "name": subsystem.name,
                "role": subsystem.role.value,
                "availability": subsystem.availability.value,
                "operational_health": subsystem.operational_health.value,
                "freshness": subsystem.freshness.value,
                "evidence_origin": subsystem.evidence_origin.value,
                "summary": sanitize_diagnostic_text(subsystem.summary),
                "details": {
                    detail.key: _safe_value(detail.value)
                    for detail in _safe_details(subsystem.details)
                },
            }
            for subsystem in snapshot.subsystems
        ],
        "runtime_metrics": [
            {
                "operation": metric.operation,
                "sample_count": metric.sample_count,
                "failure_count": metric.failure_count,
                "last_ms": metric.last_ms,
                "p50_ms": metric.p50_ms,
                "p95_ms": metric.p95_ms,
            }
            for metric in snapshot.runtime_metrics
        ],
    }


def render_doctor_json(snapshot: SystemHealthSnapshot) -> str:
    return json.dumps(doctor_json_document(snapshot), indent=2, sort_keys=True)


def sanitize_diagnostic_text(value: str) -> str:
    sanitized = _EMAIL_RE.sub("<redacted-email>", value)
    sanitized = _BEARER_RE.sub("Bearer <redacted-token>", sanitized)
    sanitized = _JWT_RE.sub("<redacted-token>", sanitized)
    sanitized = _OPENAI_TOKEN_RE.sub("<redacted-token>", sanitized)
    return _SECRET_ASSIGNMENT_RE.sub(r"\1=<redacted>", sanitized)


def _safe_details(details: Sequence[DiagnosticDetail]) -> tuple[DiagnosticDetail, ...]:
    safe: list[DiagnosticDetail] = []
    for detail in details:
        lowered = detail.key.lower()
        if any(marker in lowered for marker in _SENSITIVE_DETAIL_MARKERS):
            continue
        value = detail.value
        if isinstance(value, str):
            value = sanitize_diagnostic_text(value)
        safe.append(DiagnosticDetail(detail.key, value))
    return tuple(safe)


def _safe_value(value: object) -> object:
    return sanitize_diagnostic_text(value) if isinstance(value, str) else value


def _metric_text(metric: RuntimeMetricSummary) -> str:
    aggregates = [
        f"n={metric.sample_count}",
        f"failures={metric.failure_count}",
    ]
    if metric.last_ms is not None:
        aggregates.append(f"last={metric.last_ms:.3f} ms")
    if metric.p50_ms is not None:
        aggregates.append(f"p50={metric.p50_ms:.3f} ms")
    if metric.p95_ms is not None:
        aggregates.append(f"p95={metric.p95_ms:.3f} ms")
    return f"- {metric.operation}: " + ", ".join(aggregates)


def subsystem_map(
    snapshot: SystemHealthSnapshot,
) -> Mapping[SubsystemRole, tuple[SubsystemHealth, ...]]:
    grouped: dict[SubsystemRole, list[SubsystemHealth]] = {}
    for subsystem in snapshot.subsystems:
        grouped.setdefault(subsystem.role, []).append(subsystem)
    return {role: tuple(items) for role, items in grouped.items()}
