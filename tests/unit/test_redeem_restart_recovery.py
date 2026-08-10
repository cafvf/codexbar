from datetime import UTC, datetime

from codexbar.application.account_operations import AccountOperationCoordinator
from codexbar.application.redeem import RedeemProcessManager, RedeemProcessStatus
from codexbar.application.reset_events import (
    RedeemAttemptId,
    RedeemRequested,
    RedeemTerminal,
    ResetEvent,
    ResetEventId,
    ResetEventProvenance,
    ResetEventType,
    SequencedResetEvent,
)

NOW = datetime(2026, 8, 10, 18, tzinfo=UTC)


class Repo:
    def __init__(self, events):
        self.events = list(events)

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


class Never:
    def __getattr__(self, name):
        raise AssertionError(name)


def event(event_id, event_type, payload):
    return ResetEvent(
        ResetEventId(event_id),
        event_type,
        NOW,
        ResetEventProvenance.USER_ACTION,
        payload,
    )


def test_restart_exposes_requested_and_unknown_attempts_only() -> None:
    repo = Repo(
        [
            event(
                "e1",
                ResetEventType.REDEEM_REQUESTED,
                RedeemRequested(RedeemAttemptId("a1")),
            ),
            event(
                "e2",
                ResetEventType.REDEEM_REQUESTED,
                RedeemRequested(RedeemAttemptId("a2")),
            ),
            event(
                "e3",
                ResetEventType.REDEEM_OUTCOME_UNKNOWN,
                RedeemTerminal(RedeemAttemptId("a2")),
            ),
            event(
                "e4",
                ResetEventType.REDEEM_REQUESTED,
                RedeemRequested(RedeemAttemptId("done")),
            ),
            event(
                "e5",
                ResetEventType.REDEEM_SUCCEEDED,
                RedeemTerminal(RedeemAttemptId("done")),
            ),
        ]
    )
    manager = RedeemProcessManager(
        repo,
        Never(),
        Never(),
        AccountOperationCoordinator(),
    )

    attempts = manager.unresolved_attempts()

    assert [(a.attempt_id.value, a.status) for a in attempts] == [
        ("a1", RedeemProcessStatus.REQUESTED),
        ("a2", RedeemProcessStatus.OUTCOME_UNKNOWN),
    ]
