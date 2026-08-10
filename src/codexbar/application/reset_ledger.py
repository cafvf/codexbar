from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from codexbar.application.reset_events import ResetEvent, SequencedResetEvent
from codexbar.domain.errors import CodexBarError


class ResetLedgerError(CodexBarError):
    """Base class for expected reset-ledger failures."""


class ResetLedgerReadError(ResetLedgerError):
    pass


class ResetLedgerWriteError(ResetLedgerError):
    pass


class ResetLedgerSchemaError(ResetLedgerError):
    pass


class ResetLedgerCorruptionError(ResetLedgerReadError):
    pass


class ResetLedgerState(StrEnum):
    ABSENT = "absent"
    READY_EMPTY = "ready_empty"
    READY_NON_EMPTY = "ready_non_empty"
    UNREADABLE = "unreadable"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ResetLedgerInspection:
    path: str
    state: ResetLedgerState
    schema_version: int | None = None
    event_count: int | None = None
    oldest_occurred_at: datetime | None = None
    newest_occurred_at: datetime | None = None
    unresolved_attempt_count: int | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("reset ledger path must not be blank")
        if self.schema_version is not None and self.schema_version <= 0:
            raise ValueError("schema_version must be positive")
        if self.event_count is not None and self.event_count < 0:
            raise ValueError("event_count must not be negative")
        if self.unresolved_attempt_count is not None and self.unresolved_attempt_count < 0:
            raise ValueError("unresolved_attempt_count must not be negative")


class ResetEventRepository(Protocol):
    def append(self, event: ResetEvent) -> bool: ...

    def append_many(self, events: tuple[ResetEvent, ...]) -> int: ...

    def query_all(self) -> tuple[SequencedResetEvent, ...]: ...

    def inspect(self) -> ResetLedgerInspection: ...
