from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codexbar.application.reset_events import (
    CountChanged,
    CoverageChanged,
    CreditDetailChanged,
    CreditDiscovered,
    CreditRemoved,
    DeadlinePassed,
    InventoryBaseline,
    RedeemRequested,
    RedeemTerminal,
    ResetEventType,
    SequencedResetEvent,
)
from codexbar.domain.reset import DetailCoverage, ResetCreditDetail, ResetCreditId


class RedeemAttemptState(StrEnum):
    REQUESTED = "requested"
    SUCCEEDED = "succeeded"
    ALREADY_REDEEMED = "already_redeemed"
    REJECTED = "rejected"
    OUTCOME_UNKNOWN = "outcome_unknown"


@dataclass(frozen=True, slots=True)
class KnownRemoval:
    credit_id: ResetCreditId
    sequence: int


@dataclass(frozen=True, slots=True)
class ResetLedgerProjection:
    last_count: int | None = None
    last_coverage: DetailCoverage | None = None
    known_details: tuple[ResetCreditDetail, ...] = ()
    known_removals: tuple[KnownRemoval, ...] = ()
    signaled_deadlines: tuple[ResetCreditId, ...] = ()
    redeem_attempts: tuple[tuple[str, RedeemAttemptState], ...] = ()

    def detail_map(self) -> dict[str, ResetCreditDetail]:
        return {detail.credit_id.value: detail for detail in self.known_details}

    def attempt_map(self) -> dict[str, RedeemAttemptState]:
        return dict(self.redeem_attempts)

    @property
    def unresolved_attempt_ids(self) -> tuple[str, ...]:
        return tuple(
            attempt_id
            for attempt_id, state in self.redeem_attempts
            if state in {RedeemAttemptState.REQUESTED, RedeemAttemptState.OUTCOME_UNKNOWN}
        )


def fold_reset_events(events: tuple[SequencedResetEvent, ...]) -> ResetLedgerProjection:
    count: int | None = None
    coverage: DetailCoverage | None = None
    details: dict[str, ResetCreditDetail] = {}
    removals: list[KnownRemoval] = []
    deadlines: set[str] = set()
    attempts: dict[str, RedeemAttemptState] = {}

    for record in sorted(events, key=lambda item: item.sequence):
        event = record.event
        payload = event.payload

        if event.event_type is ResetEventType.INVENTORY_BASELINE:
            assert isinstance(payload, InventoryBaseline)
            count = payload.available_count
            coverage = payload.coverage
        elif event.event_type is ResetEventType.COUNT_CHANGED:
            assert isinstance(payload, CountChanged)
            count = payload.current_count
        elif event.event_type is ResetEventType.COVERAGE_CHANGED:
            assert isinstance(payload, CoverageChanged)
            coverage = payload.current
        elif event.event_type is ResetEventType.CREDIT_DISCOVERED:
            assert isinstance(payload, CreditDiscovered)
            details[payload.detail.credit_id.value] = payload.detail
        elif event.event_type is ResetEventType.CREDIT_DETAIL_CHANGED:
            assert isinstance(payload, CreditDetailChanged)
            details[payload.current.credit_id.value] = payload.current
        elif event.event_type is ResetEventType.CREDIT_REMOVED:
            assert isinstance(payload, CreditRemoved)
            details.pop(payload.credit_id.value, None)
            removals.append(KnownRemoval(payload.credit_id, record.sequence))
        elif event.event_type is ResetEventType.DEADLINE_PASSED:
            assert isinstance(payload, DeadlinePassed)
            deadlines.add(payload.credit_id.value)
        elif event.event_type is ResetEventType.REDEEM_REQUESTED:
            assert isinstance(payload, RedeemRequested)
            attempts[payload.attempt_id.value] = RedeemAttemptState.REQUESTED
        elif event.event_type in {
            ResetEventType.REDEEM_SUCCEEDED,
            ResetEventType.REDEEM_ALREADY_REDEEMED,
            ResetEventType.REDEEM_REJECTED,
            ResetEventType.REDEEM_OUTCOME_UNKNOWN,
        }:
            assert isinstance(payload, RedeemTerminal)
            state = {
                ResetEventType.REDEEM_SUCCEEDED: RedeemAttemptState.SUCCEEDED,
                ResetEventType.REDEEM_ALREADY_REDEEMED: RedeemAttemptState.ALREADY_REDEEMED,
                ResetEventType.REDEEM_REJECTED: RedeemAttemptState.REJECTED,
                ResetEventType.REDEEM_OUTCOME_UNKNOWN: RedeemAttemptState.OUTCOME_UNKNOWN,
            }[event.event_type]
            attempts[payload.attempt_id.value] = state

    return ResetLedgerProjection(
        last_count=count,
        last_coverage=coverage,
        known_details=tuple(sorted(details.values(), key=lambda item: item.credit_id.value)),
        known_removals=tuple(removals),
        signaled_deadlines=tuple(ResetCreditId(value) for value in sorted(deadlines)),
        redeem_attempts=tuple(sorted(attempts.items())),
    )
