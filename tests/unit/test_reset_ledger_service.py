from datetime import UTC, datetime

from codexbar.application.reset_ledger import ResetLedgerWriteError
from codexbar.application.reset_ledger_service import ResetLedgerService
from codexbar.domain.reset import DetailCoverage, ResetCreditInventory, ResetCreditReadResult

OBS = datetime(2026, 8, 10, 12, tzinfo=UTC)


class Repository:
    def __init__(self, *, fail=False):
        self.events = []
        self.fail = fail

    def query_all(self):
        from codexbar.application.reset_events import SequencedResetEvent
        return tuple(
            SequencedResetEvent(i + 1, event)
            for i, event in enumerate(self.events)
        )

    def append(self, event):
        return bool(self.append_many((event,)))

    def append_many(self, events):
        if self.fail:
            raise ResetLedgerWriteError("disk full")
        self.events.extend(events)
        return len(events)

    def inspect(self):
        raise AssertionError


def test_service_persists_derived_events_and_deduplicates_unchanged_poll() -> None:
    repository = Repository()
    service = ResetLedgerService(repository)
    result = ResetCreditReadResult.current(
        ResetCreditInventory(OBS, 2, DetailCoverage.COUNT_ONLY)
    )

    first = service.process(result)
    second = service.process(result)

    assert first.appended_count == 1
    assert second.appended_count == 0


def test_ordinary_ledger_failure_is_diagnostic_not_current_state_failure() -> None:
    service = ResetLedgerService(Repository(fail=True))
    result = ResetCreditReadResult.current(
        ResetCreditInventory(OBS, 2, DetailCoverage.COUNT_ONLY)
    )

    processed = service.process(result)

    assert processed.diagnostic is not None
