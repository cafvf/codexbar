from __future__ import annotations

import math
import time
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from threading import RLock

RUNTIME_METRIC_CAPACITY = 64


class DiagnosticAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"


class OperationalHealth(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


class EvidenceOrigin(StrEnum):
    LIVE_RUNTIME = "live_runtime"
    LOCAL_PERSISTED_INSPECTION = "local_persisted_inspection"
    FRESH_READ_ONLY_PROBE = "fresh_read_only_probe"
    UNAVAILABLE = "unavailable"


class DiagnosticFreshness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class OverallHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    NEEDS_ATTENTION = "needs_attention"


class SubsystemRole(StrEnum):
    SOURCE = "source"
    CURRENT = "current"
    HISTORY = "history"
    CONTEXT = "context"
    RESET_LEDGER = "reset_ledger"
    NATIVE_INDICATOR = "native_indicator"
    QT_FALLBACK = "qt_fallback"
    SETTINGS = "settings"
    ENVIRONMENT = "environment"
    LINEAGE = "lineage"
    INSTANCE_OWNERSHIP = "instance_ownership"
    DIAGNOSTICS = "diagnostics"


DiagnosticScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class DiagnosticDetail:
    key: str
    value: DiagnosticScalar

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("diagnostic detail key must not be blank")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("diagnostic float detail must be finite")


@dataclass(frozen=True, slots=True)
class SubsystemHealth:
    name: str
    role: SubsystemRole
    availability: DiagnosticAvailability
    operational_health: OperationalHealth
    evidence_origin: EvidenceOrigin
    summary: str
    freshness: DiagnosticFreshness = DiagnosticFreshness.UNKNOWN
    details: tuple[DiagnosticDetail, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("subsystem name must not be blank")
        if not self.summary.strip():
            raise ValueError("subsystem summary must not be blank")
        keys = [detail.key for detail in self.details]
        if len(keys) != len(set(keys)):
            raise ValueError("diagnostic detail keys must be unique per subsystem")


@dataclass(frozen=True, slots=True)
class RuntimeMetricSample:
    duration_ms: float
    succeeded: bool = True

    def __post_init__(self) -> None:
        if not math.isfinite(self.duration_ms) or self.duration_ms < 0:
            raise ValueError("runtime metric duration must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class RuntimeMetricSummary:
    operation: str
    sample_count: int
    failure_count: int
    last_ms: float | None
    p50_ms: float | None
    p95_ms: float | None

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("runtime metric operation must not be blank")
        if self.sample_count < 0:
            raise ValueError("runtime metric sample count must not be negative")
        if not 0 <= self.failure_count <= self.sample_count:
            raise ValueError("runtime metric failure count must be within sample count")
        if self.sample_count == 0 and self.last_ms is not None:
            raise ValueError("empty runtime metric summary cannot expose last")
        if self.sample_count < 3 and self.p50_ms is not None:
            raise ValueError("p50 requires at least 3 samples")
        if self.sample_count < 20 and self.p95_ms is not None:
            raise ValueError("p95 requires at least 20 samples")


class RuntimeMetricCollector:
    """Thread-safe bounded local runtime metrics with no persistence or telemetry."""

    def __init__(
        self,
        *,
        capacity: int = RUNTIME_METRIC_CAPACITY,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if capacity != RUNTIME_METRIC_CAPACITY:
            raise ValueError(f"runtime metric capacity must be {RUNTIME_METRIC_CAPACITY}")
        self._capacity = capacity
        self._monotonic = monotonic or time.monotonic
        self._samples: dict[str, deque[RuntimeMetricSample]] = {}
        self._lock = RLock()

    @property
    def capacity(self) -> int:
        return self._capacity

    def record(self, operation: str, duration_ms: float, *, succeeded: bool = True) -> None:
        if not operation.strip():
            raise ValueError("runtime metric operation must not be blank")
        sample = RuntimeMetricSample(duration_ms=duration_ms, succeeded=succeeded)
        with self._lock:
            bucket = self._samples.setdefault(operation, deque(maxlen=self._capacity))
            bucket.append(sample)

    @contextmanager
    def measure(self, operation: str) -> Iterator[None]:
        start = self._monotonic()
        try:
            yield
        except Exception:
            self._record_elapsed(operation, start, succeeded=False)
            raise
        else:
            self._record_elapsed(operation, start, succeeded=True)

    def retained_samples(self, operation: str) -> tuple[RuntimeMetricSample, ...]:
        with self._lock:
            return tuple(self._samples.get(operation, ()))

    def summary(self, operation: str) -> RuntimeMetricSummary:
        samples = self.retained_samples(operation)
        durations = tuple(sample.duration_ms for sample in samples)
        count = len(samples)
        return RuntimeMetricSummary(
            operation=operation,
            sample_count=count,
            failure_count=sum(not sample.succeeded for sample in samples),
            last_ms=durations[-1] if durations else None,
            p50_ms=_empirical_quantile(durations, 0.50) if count >= 3 else None,
            p95_ms=_empirical_quantile(durations, 0.95) if count >= 20 else None,
        )

    def snapshot(self) -> tuple[RuntimeMetricSummary, ...]:
        with self._lock:
            operations = tuple(sorted(self._samples))
        return tuple(self.summary(operation) for operation in operations)

    def _record_elapsed(self, operation: str, start: float, *, succeeded: bool) -> None:
        end = self._monotonic()
        elapsed = end - start
        if elapsed < 0:
            raise ValueError("monotonic clock moved backwards")
        self.record(operation, elapsed * 1000.0, succeeded=succeeded)


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    """Linear interpolation at fractional index (N - 1) * p."""
    if not values:
        raise ValueError("runtime metric quantile requires at least one sample")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("runtime metric probability must be within [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * probability
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = index - lower_index
    lower = ordered[lower_index]
    upper = ordered[upper_index]
    return lower + (upper - lower) * fraction


@dataclass(frozen=True, slots=True)
class SystemHealthSnapshot:
    generated_at: datetime
    subsystems: tuple[SubsystemHealth, ...]
    runtime_metrics: tuple[RuntimeMetricSummary, ...] = ()

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("health snapshot generated_at must be timezone-aware")
        names = [subsystem.name for subsystem in self.subsystems]
        if len(names) != len(set(names)):
            raise ValueError("health snapshot subsystem names must be unique")

    @property
    def overall_health(self) -> OverallHealth:
        return derive_overall_health(self.subsystems)


def derive_overall_health(subsystems: Sequence[SubsystemHealth]) -> OverallHealth:
    """Derive DEC-1703 presentation health without collapsing source dimensions."""
    by_role: dict[SubsystemRole, list[SubsystemHealth]] = {}
    for subsystem in subsystems:
        by_role.setdefault(subsystem.role, []).append(subsystem)

    instance = by_role.get(SubsystemRole.INSTANCE_OWNERSHIP, ())
    if any(item.operational_health is OperationalHealth.FAILED for item in instance):
        return OverallHealth.NEEDS_ATTENTION

    current_items = by_role.get(SubsystemRole.CURRENT, ())
    source_items = by_role.get(SubsystemRole.SOURCE, ())
    current_usable = any(
        item.availability is DiagnosticAvailability.AVAILABLE
        and item.operational_health is not OperationalHealth.FAILED
        for item in current_items
    )
    source_usable = any(
        item.availability is DiagnosticAvailability.AVAILABLE
        and item.operational_health is not OperationalHealth.FAILED
        for item in source_items
    )
    if (current_items or source_items) and not current_usable and not source_usable:
        return OverallHealth.NEEDS_ATTENTION

    source_failed = any(
        item.operational_health is OperationalHealth.FAILED for item in source_items
    )
    current_failed = any(
        item.operational_health is OperationalHealth.FAILED for item in current_items
    )

    if (source_failed or current_failed) and not current_usable:
        return OverallHealth.NEEDS_ATTENTION

    if any(item.freshness is DiagnosticFreshness.STALE for item in current_items):
        return OverallHealth.DEGRADED

    if source_failed and current_usable:
        return OverallHealth.DEGRADED

    qt_fallback_healthy = any(
        item.availability is DiagnosticAvailability.AVAILABLE
        and item.operational_health is OperationalHealth.OK
        for item in by_role.get(SubsystemRole.QT_FALLBACK, ())
    )

    for subsystem in subsystems:
        if subsystem.role is SubsystemRole.NATIVE_INDICATOR and qt_fallback_healthy:
            continue
        if subsystem.operational_health in {
            OperationalHealth.DEGRADED,
            OperationalHealth.FAILED,
        }:
            return OverallHealth.DEGRADED

    return OverallHealth.HEALTHY
