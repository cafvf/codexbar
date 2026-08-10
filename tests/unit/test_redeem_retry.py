from contextlib import suppress
from datetime import UTC, datetime

from codexbar.application.account import ResetConsumeOutcome
from codexbar.application.account_operations import AccountOperationCoordinator
from codexbar.application.redeem import RedeemProcessManager, RedeemProcessStatus
from codexbar.application.reset_events import RedeemAttemptId, ResetEventId, SequencedResetEvent
from codexbar.domain.errors import UsageTimeoutError

NOW = datetime(2026, 8, 10, 18, tzinfo=UTC)


class Repo:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)
        return True

    def append_many(self, events):
        self.events.extend(events)
        return len(events)

    def query_all(self):
        return tuple(
            SequencedResetEvent(i + 1, event)
            for i, event in enumerate(self.events)
        )

    def inspect(self):
        raise AssertionError


class Consumer:
    def __init__(self):
        self.calls = 0
        self.keys = []

    def consume_reset_credit(self, command):
        self.calls += 1
        self.keys.append(command.attempt_id.value)
        if self.calls == 1:
            raise UsageTimeoutError("possible send")
        return ResetConsumeOutcome.ALREADY_REDEEMED


class Reader:
    def read_account_rate_limits(self):
        raise AssertionError("fixture only tests idempotency key before refetch")


def test_retry_reuses_exact_same_attempt_and_idempotency_key() -> None:
    repo = Repo()
    consumer = Consumer()
    ids = iter(["event-1", "event-2", "event-3"])
    manager = RedeemProcessManager(
        repo,
        consumer,
        Reader(),
        AccountOperationCoordinator(),
        clock=lambda: NOW,
        attempt_id_factory=lambda: RedeemAttemptId("attempt-fixed"),
        event_id_factory=lambda: ResetEventId(next(ids)),
    )

    first = manager.redeem()
    assert first.attempt.status is RedeemProcessStatus.OUTCOME_UNKNOWN

    with suppress(AssertionError):
        manager.retry(first.attempt.attempt_id)

    assert consumer.keys == ["attempt-fixed", "attempt-fixed"]
