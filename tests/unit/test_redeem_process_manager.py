from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.application.account import (
    AccountRateLimitsObservation,
    ResetConsumeOutcome,
)
from codexbar.application.account_operations import AccountOperationCoordinator
from codexbar.application.redeem import (
    RedeemAttemptId,
    RedeemBeginError,
    RedeemProcessManager,
    RedeemProcessStatus,
)
from codexbar.application.reset_events import ResetEventId, ResetEventType, SequencedResetEvent
from codexbar.application.reset_ledger import ResetLedgerWriteError
from codexbar.domain.errors import (
    UsageSchemaError,
    UsageSourceUnavailableError,
    UsageTimeoutError,
)
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import ResetCreditReadResult

NOW = datetime(2026, 8, 10, 18, tzinfo=UTC)


def observation():
    return AccountRateLimitsObservation(
        UsageSnapshot(
            (
                UsageWindow(
                    UsageWindowId("window_300m"),
                    "5 hours",
                    Fraction(Decimal("1")),
                ),
            ),
            NOW,
            UsageSource.MOCK,
        ),
        ResetCreditReadResult.unavailable("fixture"),
    )


class Repo:
    def __init__(self, *, fail=False):
        self.events = []
        self.fail = fail

    def append(self, event):
        if self.fail:
            raise ResetLedgerWriteError("disk failure")
        if any(item.event_id == event.event_id for item in self.events):
            return False
        self.events.append(event)
        return True

    def append_many(self, events):
        return sum(self.append(event) for event in events)

    def query_all(self):
        return tuple(
            SequencedResetEvent(index + 1, event)
            for index, event in enumerate(self.events)
        )

    def inspect(self):
        raise AssertionError


class Consumer:
    def __init__(self, outcome=ResetConsumeOutcome.RESET, error=None):
        self.outcome = outcome
        self.error = error
        self.commands = []

    def consume_reset_credit(self, command):
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        return self.outcome


class Reader:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def read_account_rate_limits(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return observation()


class Ids:
    def __init__(self):
        self.n = 0

    def event(self):
        self.n += 1
        return ResetEventId(f"event-{self.n}")


def manager(repo, consumer, reader):
    ids = Ids()
    return RedeemProcessManager(
        repo,
        consumer,
        reader,
        AccountOperationCoordinator(),
        clock=lambda: NOW,
        attempt_id_factory=lambda: RedeemAttemptId("attempt-1"),
        event_id_factory=ids.event,
    )


def test_requested_is_durable_before_consumer_and_success_refetches() -> None:
    repo = Repo()

    class OrderingConsumer(Consumer):
        def consume_reset_credit(self, command):
            assert repo.events[-1].event_type is ResetEventType.REDEEM_REQUESTED
            return super().consume_reset_credit(command)

    consumer = OrderingConsumer()
    reader = Reader()
    result = manager(repo, consumer, reader).redeem()

    assert result.attempt.status is RedeemProcessStatus.SUCCEEDED
    assert reader.calls == 1
    assert [event.event_type for event in repo.events] == [
        ResetEventType.REDEEM_REQUESTED,
        ResetEventType.REDEEM_SUCCEEDED,
    ]


def test_ledger_failure_before_begin_blocks_consumer() -> None:
    repo = Repo(fail=True)
    consumer = Consumer()

    with pytest.raises(RedeemBeginError):
        manager(repo, consumer, Reader()).redeem()

    assert consumer.commands == []


@pytest.mark.parametrize(
    "outcome",
    [ResetConsumeOutcome.NOTHING_TO_RESET, ResetConsumeOutcome.NO_CREDIT],
)
def test_rejected_outcomes_do_not_refetch(outcome) -> None:
    reader = Reader()
    result = manager(Repo(), Consumer(outcome), reader).redeem()

    assert result.attempt.status is RedeemProcessStatus.REJECTED
    assert reader.calls == 0


def test_timeout_after_possible_send_is_outcome_unknown() -> None:
    result = manager(
        Repo(),
        Consumer(error=UsageTimeoutError("timeout")),
        Reader(),
    ).redeem()

    assert result.attempt.status is RedeemProcessStatus.OUTCOME_UNKNOWN


@pytest.mark.parametrize(
    "refetch_error",
    [
        UsageSourceUnavailableError("offline"),
        UsageSchemaError("unsupported response shape"),
    ],
)
def test_success_plus_expected_refetch_failure_preserves_success(refetch_error) -> None:
    result = manager(
        Repo(),
        Consumer(),
        Reader(error=refetch_error),
    ).redeem()

    assert result.attempt.status is RedeemProcessStatus.SUCCEEDED
    assert result.observation is None
    assert result.refetch_error is refetch_error
