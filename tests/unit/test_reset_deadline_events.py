from datetime import UTC, datetime

from codexbar.application.reset_deadlines import ResetDeadlineService
from codexbar.application.reset_ledger_service import ResetLedgerService
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
    ResetCreditReadResult,
)


class Repository:
    def __init__(self):
        self.events = []

    def query_all(self):
        from codexbar.application.reset_events import SequencedResetEvent
        return tuple(
            SequencedResetEvent(i + 1, event)
            for i, event in enumerate(self.events)
        )

    def append(self, event):
        return bool(self.append_many((event,)))

    def append_many(self, events):
        self.events.extend(events)
        return len(events)

    def inspect(self):
        raise AssertionError


def test_expiring_deadline_is_recorded_once_non_expiring_is_never_recorded() -> None:
    repo = Repository()
    ledger = ResetLedgerService(repo)
    observed = datetime(2026, 8, 10, 10, tzinfo=UTC)
    expiry = datetime(2026, 8, 10, 11, tzinfo=UTC)
    inventory = ResetCreditInventory(
        observed,
        2,
        DetailCoverage.DETAILS_COMPLETE,
        (
            ResetCreditDetail(
                ResetCreditId("A"),
                "codexRateLimits",
                "available",
                observed,
                ExpiryKnowledge.expires_at(expiry),
            ),
            ResetCreditDetail(
                ResetCreditId("B"),
                "codexRateLimits",
                "available",
                observed,
                ExpiryKnowledge.does_not_expire(),
            ),
        ),
    )
    ledger.process(ResetCreditReadResult.current(inventory))
    service = ResetDeadlineService(
        repo,
        clock=lambda: datetime(2026, 8, 10, 12, tzinfo=UTC),
    )

    assert service.record_passed_known_deadlines() == 1
    assert service.record_passed_known_deadlines() == 0
