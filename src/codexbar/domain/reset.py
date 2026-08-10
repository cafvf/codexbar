from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class ResetCreditId:
    """Opaque reset-credit identity supplied by the upstream account boundary."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("reset credit id must not be blank")


class DetailCoverage(StrEnum):
    COUNT_ONLY = "count_only"
    DETAILS_PARTIAL = "details_partial"
    DETAILS_COMPLETE = "details_complete"


class ExpiryKind(StrEnum):
    EXPIRES_AT = "expires_at"
    DOES_NOT_EXPIRE = "does_not_expire"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExpiryKnowledge:
    """Explicit knowledge about one credit's expiry semantics."""

    kind: ExpiryKind
    instant: datetime | None = None

    def __post_init__(self) -> None:
        if self.kind is ExpiryKind.EXPIRES_AT:
            if self.instant is None:
                raise ValueError("expiring credit requires an expiry instant")
            if self.instant.tzinfo is None or self.instant.utcoffset() is None:
                raise ValueError("expiry instant must be timezone-aware")
            object.__setattr__(self, "instant", self.instant.astimezone(UTC))
            return

        if self.instant is not None:
            raise ValueError("non-concrete expiry knowledge must not carry an instant")

    @classmethod
    def expires_at(cls, instant: datetime) -> ExpiryKnowledge:
        return cls(kind=ExpiryKind.EXPIRES_AT, instant=instant)

    @classmethod
    def does_not_expire(cls) -> ExpiryKnowledge:
        return cls(kind=ExpiryKind.DOES_NOT_EXPIRE)

    @classmethod
    def unknown(cls) -> ExpiryKnowledge:
        return cls(kind=ExpiryKind.UNKNOWN)


@dataclass(frozen=True, slots=True)
class ResetCreditDetail:
    credit_id: ResetCreditId
    reset_type: str
    status: str
    granted_at: datetime
    expiry: ExpiryKnowledge
    title: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.reset_type.strip():
            raise ValueError("reset credit type must not be blank")
        if not self.status.strip():
            raise ValueError("reset credit status must not be blank")
        if self.granted_at.tzinfo is None or self.granted_at.utcoffset() is None:
            raise ValueError("granted_at must be timezone-aware")
        object.__setattr__(self, "granted_at", self.granted_at.astimezone(UTC))

        if self.expiry.kind is ExpiryKind.UNKNOWN:
            raise ValueError("detailed reset credit expiry must be known")


@dataclass(frozen=True, slots=True)
class ResetCreditInventory:
    observed_at: datetime
    available_count: int
    detail_coverage: DetailCoverage
    credits: tuple[ResetCreditDetail, ...] = ()

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if isinstance(self.available_count, bool) or not isinstance(self.available_count, int):
            raise ValueError("available_count must be an integer")
        if self.available_count < 0:
            raise ValueError("available_count must not be negative")

        ids = [credit.credit_id.value for credit in self.credits]
        if len(ids) != len(set(ids)):
            raise ValueError("reset credit ids must be unique within an inventory")

        detail_count = len(self.credits)
        if detail_count > self.available_count:
            raise ValueError("reset credit detail count must not exceed available_count")
        if self.detail_coverage is DetailCoverage.COUNT_ONLY and detail_count != 0:
            raise ValueError("COUNT_ONLY inventory must not contain credit details")
        if self.detail_coverage is DetailCoverage.DETAILS_PARTIAL and not (
            detail_count < self.available_count
        ):
            raise ValueError(
                "DETAILS_PARTIAL inventory requires fewer details than available_count"
            )
        if self.detail_coverage is DetailCoverage.DETAILS_COMPLETE and (
            detail_count != self.available_count
        ):
            raise ValueError("DETAILS_COMPLETE inventory requires one detail per available credit")


class ResetCreditReadStatus(StrEnum):
    CURRENT = "current"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ResetCreditReadResult:
    status: ResetCreditReadStatus
    inventory: ResetCreditInventory | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.status is ResetCreditReadStatus.CURRENT:
            if self.inventory is None:
                raise ValueError("CURRENT reset-credit result requires an inventory")
            if self.diagnostic is not None:
                raise ValueError("CURRENT reset-credit result must not carry a diagnostic")
            return

        if self.inventory is not None:
            raise ValueError("UNAVAILABLE reset-credit result must not carry an inventory")
        if self.diagnostic is not None and not self.diagnostic.strip():
            raise ValueError("reset-credit diagnostic must not be blank")

    @classmethod
    def current(cls, inventory: ResetCreditInventory) -> ResetCreditReadResult:
        return cls(status=ResetCreditReadStatus.CURRENT, inventory=inventory)

    @classmethod
    def unavailable(cls, diagnostic: str | None = None) -> ResetCreditReadResult:
        return cls(status=ResetCreditReadStatus.UNAVAILABLE, diagnostic=diagnostic)
