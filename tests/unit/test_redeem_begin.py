from datetime import UTC, datetime

import pytest

from codexbar.application.account_operations import AccountOperationCoordinator
from codexbar.application.redeem import (
    RedeemAttemptId,
    RedeemBeginError,
    RedeemProcessManager,
)
from codexbar.application.reset_events import ResetEventId
from codexbar.application.reset_ledger import ResetLedgerWriteError

NOW = datetime(2026, 8, 10, 18, tzinfo=UTC)


class FailingRepo:
    def append(self, event):
        raise ResetLedgerWriteError("disk")

    def append_many(self, events):
        raise ResetLedgerWriteError("disk")

    def query_all(self):
        return ()

    def inspect(self):
        raise AssertionError


class Never:
    def __getattr__(self, name):
        raise AssertionError(name)


def test_begin_fails_closed_when_requested_event_cannot_commit() -> None:
    manager = RedeemProcessManager(
        FailingRepo(),
        Never(),
        Never(),
        AccountOperationCoordinator(),
        clock=lambda: NOW,
        attempt_id_factory=lambda: RedeemAttemptId("attempt-1"),
        event_id_factory=lambda: ResetEventId("event-1"),
    )

    with pytest.raises(RedeemBeginError):
        manager.begin()
