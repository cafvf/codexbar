from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from codexbar.domain.errors import CodexBarError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindowId,
)


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class HistoryInterval:
    """Half-open history query interval [start, end)."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_aware(self.start, "start")
        _require_aware(self.end, "end")
        if self.start >= self.end:
            raise ValueError("history interval start must be earlier than end")

    def contains(self, observed_at: datetime) -> bool:
        _require_aware(observed_at, "observed_at")
        return self.start <= observed_at < self.end


@dataclass(frozen=True, slots=True)
class HistoricalWindowObservation:
    window_id: UsageWindowId
    label: str
    remaining: Fraction
    resets_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("historical window label must not be blank")
        if self.resets_at is not None:
            _require_aware(self.resets_at, "resets_at")


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot:
    observed_at: datetime
    source: UsageSource
    windows: tuple[HistoricalWindowObservation, ...]
    rate_limit_reached_type: str | None = None

    def __post_init__(self) -> None:
        _require_aware(self.observed_at, "observed_at")
        ids = [window.window_id.value for window in self.windows]
        if len(ids) != len(set(ids)):
            raise ValueError("historical window ids must be unique within a snapshot")

    @classmethod
    def from_usage_snapshot(cls, snapshot: UsageSnapshot) -> HistoricalSnapshot:
        if snapshot.freshness is not Freshness.CURRENT:
            raise ValueError("only CURRENT snapshots are eligible for history")
        return cls(
            observed_at=snapshot.observed_at,
            source=snapshot.source,
            windows=tuple(
                HistoricalWindowObservation(
                    window_id=window.id,
                    label=window.label,
                    remaining=window.remaining,
                    resets_at=window.resets_at,
                )
                for window in snapshot.windows
            ),
            rate_limit_reached_type=snapshot.rate_limit_reached_type,
        )


@dataclass(frozen=True, slots=True)
class HistoricalWindowSample:
    """One window observation together with its historical time context."""

    observed_at: datetime
    source: UsageSource
    observation: HistoricalWindowObservation

    def __post_init__(self) -> None:
        _require_aware(self.observed_at, "observed_at")


class HistoryState(StrEnum):
    ABSENT = "absent"
    READY_EMPTY = "ready_empty"
    READY_NON_EMPTY = "ready_non_empty"
    UNREADABLE = "unreadable"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class HistoryInspection:
    path: str
    state: HistoryState
    schema_version: int | None = None
    snapshot_count: int | None = None
    oldest_observed_at: datetime | None = None
    newest_observed_at: datetime | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("history path must not be blank")
        if self.schema_version is not None and self.schema_version <= 0:
            raise ValueError("history schema version must be positive")
        if self.snapshot_count is not None and self.snapshot_count < 0:
            raise ValueError("snapshot_count must not be negative")
        for field_name, value in (
            ("oldest_observed_at", self.oldest_observed_at),
            ("newest_observed_at", self.newest_observed_at),
        ):
            if value is not None:
                _require_aware(value, field_name)
        if (
            self.oldest_observed_at is not None
            and self.newest_observed_at is not None
            and self.oldest_observed_at > self.newest_observed_at
        ):
            raise ValueError("oldest history observation must not be newer than newest")


class HistoryError(CodexBarError):
    """Base class for expected history failures."""


class HistoryReadError(HistoryError):
    """History could not be read or queried."""


class HistoryWriteError(HistoryError):
    """History could not be appended, pruned, or cleared."""


class HistorySchemaError(HistoryError):
    """History schema is unsupported or structurally invalid."""


class HistoryCorruptionError(HistoryReadError):
    """History storage is corrupt and must not be silently replaced."""


class HistoryRepository(Protocol):
    def append(self, snapshot: HistoricalSnapshot) -> bool: ...

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]: ...

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]: ...

    def prune(self, cutoff: datetime) -> int: ...

    def inspect(self) -> HistoryInspection: ...

    def clear(self) -> int: ...


class RecordHistorySnapshot:
    """Offer eligible CURRENT snapshots to the history repository."""

    def __init__(self, repository: HistoryRepository) -> None:
        self._repository = repository

    def execute(self, snapshot: UsageSnapshot) -> bool:
        if snapshot.freshness is not Freshness.CURRENT:
            return False
        self._repository.append(HistoricalSnapshot.from_usage_snapshot(snapshot))
        return True
