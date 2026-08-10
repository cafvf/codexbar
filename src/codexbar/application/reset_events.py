from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from codexbar.domain.reset import DetailCoverage, ResetCreditDetail, ResetCreditId


def _aware_utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ResetEventId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("reset event id must not be blank")


@dataclass(frozen=True, slots=True)
class RedeemAttemptId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("redeem attempt id must not be blank")


class ResetEventProvenance(StrEnum):
    OBSERVATION = "observation"
    USER_ACTION = "user_action"
    SYSTEM = "system"


class ResetEventType(StrEnum):
    INVENTORY_BASELINE = "inventory_baseline"
    COUNT_CHANGED = "count_changed"
    COVERAGE_CHANGED = "coverage_changed"
    CREDIT_DISCOVERED = "credit_discovered"
    CREDIT_DETAIL_CHANGED = "credit_detail_changed"
    CREDIT_REMOVED = "credit_removed"
    DEADLINE_PASSED = "deadline_passed"
    REDEEM_REQUESTED = "redeem_requested"
    REDEEM_SUCCEEDED = "redeem_succeeded"
    REDEEM_ALREADY_REDEEMED = "redeem_already_redeemed"
    REDEEM_REJECTED = "redeem_rejected"
    REDEEM_OUTCOME_UNKNOWN = "redeem_outcome_unknown"


@dataclass(frozen=True, slots=True)
class InventoryBaseline:
    available_count: int
    coverage: DetailCoverage

    def __post_init__(self) -> None:
        if self.available_count < 0:
            raise ValueError("available_count must not be negative")


@dataclass(frozen=True, slots=True)
class CountChanged:
    previous_count: int
    current_count: int

    def __post_init__(self) -> None:
        if self.previous_count < 0 or self.current_count < 0:
            raise ValueError("counts must not be negative")
        if self.previous_count == self.current_count:
            raise ValueError("count change requires different values")


@dataclass(frozen=True, slots=True)
class CoverageChanged:
    previous: DetailCoverage
    current: DetailCoverage

    def __post_init__(self) -> None:
        if self.previous is self.current:
            raise ValueError("coverage change requires different values")


@dataclass(frozen=True, slots=True)
class CreditDiscovered:
    detail: ResetCreditDetail


@dataclass(frozen=True, slots=True)
class CreditDetailChanged:
    previous: ResetCreditDetail
    current: ResetCreditDetail

    def __post_init__(self) -> None:
        if self.previous.credit_id != self.current.credit_id:
            raise ValueError("detail change must preserve credit identity")
        if self.previous == self.current:
            raise ValueError("detail change requires different values")


@dataclass(frozen=True, slots=True)
class CreditRemoved:
    credit_id: ResetCreditId


@dataclass(frozen=True, slots=True)
class DeadlinePassed:
    credit_id: ResetCreditId
    deadline: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "deadline", _aware_utc(self.deadline, "deadline"))


@dataclass(frozen=True, slots=True)
class RedeemRequested:
    attempt_id: RedeemAttemptId
    credit_id: ResetCreditId | None = None


@dataclass(frozen=True, slots=True)
class RedeemTerminal:
    attempt_id: RedeemAttemptId
    diagnostic: str | None = None


type ResetEventPayload = (
    InventoryBaseline
    | CountChanged
    | CoverageChanged
    | CreditDiscovered
    | CreditDetailChanged
    | CreditRemoved
    | DeadlinePassed
    | RedeemRequested
    | RedeemTerminal
)


@dataclass(frozen=True, slots=True)
class ResetEvent:
    event_id: ResetEventId
    event_type: ResetEventType
    occurred_at: datetime
    provenance: ResetEventProvenance
    payload: ResetEventPayload
    payload_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at", _aware_utc(self.occurred_at, "occurred_at"))
        if self.payload_version <= 0:
            raise ValueError("payload_version must be positive")


@dataclass(frozen=True, slots=True)
class SequencedResetEvent:
    sequence: int
    event: ResetEvent

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("reset event sequence must be positive")
