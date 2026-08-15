from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from codexbar.application.account import (
    AccountRateLimitsObservation,
    AccountRateLimitsReader,
    ResetConsumeCommand,
    ResetConsumeOutcome,
    ResetCreditConsumer,
)
from codexbar.application.account_operations import AccountOperationCoordinator
from codexbar.application.reset_events import (
    RedeemAttemptId,
    RedeemRequested,
    RedeemTerminal,
    ResetEvent,
    ResetEventId,
    ResetEventPayload,
    ResetEventProvenance,
    ResetEventType,
)
from codexbar.application.reset_ledger import (
    ResetEventRepository,
    ResetLedgerError,
    ResetLedgerWriteError,
)
from codexbar.application.reset_projection import RedeemAttemptState, fold_reset_events
from codexbar.domain.errors import UsageCommandError, UsageError, UsageTimeoutError
from codexbar.domain.reset import ResetCreditId


class RedeemProcessStatus(StrEnum):
    REQUESTED = "requested"
    SUCCEEDED = "succeeded"
    ALREADY_REDEEMED = "already_redeemed"
    REJECTED = "rejected"
    OUTCOME_UNKNOWN = "outcome_unknown"


@dataclass(frozen=True, slots=True)
class RedeemAttempt:
    attempt_id: RedeemAttemptId
    credit_id: ResetCreditId | None
    status: RedeemProcessStatus


@dataclass(frozen=True, slots=True)
class RedeemResult:
    attempt: RedeemAttempt
    observation: AccountRateLimitsObservation | None = None
    refetch_error: UsageError | None = None


class RedeemBeginError(RuntimeError):
    """Fail-closed error raised before any external consume may occur."""


class RedeemRecoveryError(RuntimeError):
    pass


Clock = Callable[[], datetime]
AttemptIdFactory = Callable[[], RedeemAttemptId]
EventIdFactory = Callable[[], ResetEventId]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _attempt_id() -> RedeemAttemptId:
    return RedeemAttemptId(str(uuid4()))


def _event_id() -> ResetEventId:
    return ResetEventId(str(uuid4()))


class RedeemProcessManager:
    """Durable, serialized and idempotent manual reset-credit process manager."""

    def __init__(
        self,
        repository: ResetEventRepository,
        consumer: ResetCreditConsumer,
        reader: AccountRateLimitsReader,
        coordinator: AccountOperationCoordinator,
        *,
        clock: Clock = _utc_now,
        attempt_id_factory: AttemptIdFactory = _attempt_id,
        event_id_factory: EventIdFactory = _event_id,
    ) -> None:
        self._repository = repository
        self._consumer = consumer
        self._reader = reader
        self._coordinator = coordinator
        self._clock = clock
        self._attempt_id_factory = attempt_id_factory
        self._event_id_factory = event_id_factory

    def begin(self, *, credit_id: ResetCreditId | None = None) -> RedeemAttempt:
        attempt = RedeemAttempt(
            self._attempt_id_factory(),
            credit_id,
            RedeemProcessStatus.REQUESTED,
        )
        event = self._event(
            ResetEventType.REDEEM_REQUESTED,
            RedeemRequested(attempt.attempt_id, credit_id),
        )
        try:
            appended = self._repository.append(event)
        except ResetLedgerError as exc:
            raise RedeemBeginError("cannot durably begin redeem attempt") from exc
        if not appended:
            raise RedeemBeginError("redeem attempt event was not durably appended")
        return attempt

    def redeem(self, *, credit_id: ResetCreditId | None = None) -> RedeemResult:
        attempt = self.begin(credit_id=credit_id)
        return self._coordinator.execute(lambda: self._send_and_finalize(attempt))

    def retry(self, attempt_id: RedeemAttemptId) -> RedeemResult:
        attempt = self._recover_attempt(attempt_id)
        return self._coordinator.execute(lambda: self._send_and_finalize(attempt))

    def unresolved_attempts(self) -> tuple[RedeemAttempt, ...]:
        records = self._repository.query_all()
        projection = fold_reset_events(records)
        unresolved = set(projection.unresolved_attempt_ids)
        requested: dict[str, ResetCreditId | None] = {}
        for record in records:
            event = record.event
            if event.event_type is ResetEventType.REDEEM_REQUESTED:
                payload = event.payload
                assert isinstance(payload, RedeemRequested)
                requested[payload.attempt_id.value] = payload.credit_id
        return tuple(
            RedeemAttempt(
                RedeemAttemptId(attempt_id),
                requested.get(attempt_id),
                RedeemProcessStatus.OUTCOME_UNKNOWN
                if projection.attempt_map()[attempt_id]
                is RedeemAttemptState.OUTCOME_UNKNOWN
                else RedeemProcessStatus.REQUESTED,
            )
            for attempt_id in sorted(unresolved)
        )

    def _recover_attempt(self, attempt_id: RedeemAttemptId) -> RedeemAttempt:
        matches = [
            attempt
            for attempt in self.unresolved_attempts()
            if attempt.attempt_id == attempt_id
        ]
        if not matches:
            raise RedeemRecoveryError(
                f"redeem attempt {attempt_id.value!r} is not unresolved"
            )
        return matches[0]

    def _send_and_finalize(self, attempt: RedeemAttempt) -> RedeemResult:
        command = ResetConsumeCommand(attempt.attempt_id, attempt.credit_id)
        try:
            outcome = self._consumer.consume_reset_credit(command)
        except (UsageTimeoutError, UsageCommandError) as exc:
            unknown = RedeemAttempt(
                attempt.attempt_id,
                attempt.credit_id,
                RedeemProcessStatus.OUTCOME_UNKNOWN,
            )
            self._append_terminal(
                ResetEventType.REDEEM_OUTCOME_UNKNOWN,
                unknown.attempt_id,
                diagnostic=str(exc),
            )
            return RedeemResult(unknown)

        if outcome is ResetConsumeOutcome.RESET:
            completed = RedeemAttempt(
                attempt.attempt_id,
                attempt.credit_id,
                RedeemProcessStatus.SUCCEEDED,
            )
            self._append_terminal(
                ResetEventType.REDEEM_SUCCEEDED,
                completed.attempt_id,
            )
            return self._refetch_after_success(completed)

        if outcome is ResetConsumeOutcome.ALREADY_REDEEMED:
            completed = RedeemAttempt(
                attempt.attempt_id,
                attempt.credit_id,
                RedeemProcessStatus.ALREADY_REDEEMED,
            )
            self._append_terminal(
                ResetEventType.REDEEM_ALREADY_REDEEMED,
                completed.attempt_id,
            )
            return self._refetch_after_success(completed)

        rejected = RedeemAttempt(
            attempt.attempt_id,
            attempt.credit_id,
            RedeemProcessStatus.REJECTED,
        )
        self._append_terminal(
            ResetEventType.REDEEM_REJECTED,
            rejected.attempt_id,
            diagnostic=outcome.value,
        )
        return RedeemResult(rejected)

    def _refetch_after_success(self, attempt: RedeemAttempt) -> RedeemResult:
        try:
            observation = self._reader.read_account_rate_limits()
        except UsageError as exc:
            return RedeemResult(attempt, refetch_error=exc)
        return RedeemResult(attempt, observation=observation)

    def _append_terminal(
        self,
        event_type: ResetEventType,
        attempt_id: RedeemAttemptId,
        *,
        diagnostic: str | None = None,
    ) -> None:
        try:
            appended = self._repository.append(
                self._event(
                    event_type,
                    RedeemTerminal(attempt_id, diagnostic),
                )
            )
        except ResetLedgerError as exc:
            raise ResetLedgerWriteError(
                "cannot persist redeem outcome"
            ) from exc
        if not appended:
            raise ResetLedgerWriteError("redeem outcome event was not appended")

    def _event(
        self,
        event_type: ResetEventType,
        payload: ResetEventPayload,
    ) -> ResetEvent:
        occurred_at = self._clock()
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("redeem process clock must be timezone-aware")
        return ResetEvent(
            event_id=self._event_id_factory(),
            event_type=event_type,
            occurred_at=occurred_at,
            provenance=ResetEventProvenance.USER_ACTION,
            payload=payload,
        )
