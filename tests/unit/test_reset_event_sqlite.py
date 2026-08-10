import sqlite3
from datetime import UTC, datetime

from codexbar.application.reset_events import (
    InventoryBaseline,
    RedeemAttemptId,
    RedeemRequested,
    ResetEvent,
    ResetEventId,
    ResetEventProvenance,
    ResetEventType,
)
from codexbar.application.reset_ledger import ResetLedgerState
from codexbar.domain.reset import DetailCoverage
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository


def _event(event_id: str = "evt-1") -> ResetEvent:
    return ResetEvent(
        ResetEventId(event_id),
        ResetEventType.INVENTORY_BASELINE,
        datetime(2026, 8, 10, 12, tzinfo=UTC),
        ResetEventProvenance.OBSERVATION,
        InventoryBaseline(2, DetailCoverage.COUNT_ONLY),
    )


def test_fresh_database_schema_v1_append_sequence_and_dedup(tmp_path) -> None:
    path = tmp_path / "reset.sqlite3"
    repo = SqliteResetEventRepository(path)

    assert repo.append(_event()) is True
    assert repo.append(_event()) is False

    records = repo.query_all()
    assert len(records) == 1
    assert records[0].sequence == 1
    assert repo.inspect().state is ResetLedgerState.READY_NON_EMPTY


def test_absent_inspection_does_not_create_database(tmp_path) -> None:
    path = tmp_path / "missing.sqlite3"

    inspection = SqliteResetEventRepository.inspect_path(path)

    assert inspection.state is ResetLedgerState.ABSENT
    assert not path.exists()


def test_corrupt_and_unsupported_schema_are_classified(tmp_path) -> None:
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not a sqlite database")
    assert SqliteResetEventRepository.inspect_path(corrupt).state is ResetLedgerState.UNREADABLE

    unsupported = tmp_path / "unsupported.sqlite3"
    repo = SqliteResetEventRepository(unsupported)
    del repo
    with sqlite3.connect(unsupported) as connection:
        connection.execute(
            "UPDATE reset_ledger_meta SET value='99' WHERE key='schema_version'"
        )
    assert (
        SqliteResetEventRepository.inspect_path(unsupported).state
        is ResetLedgerState.UNSUPPORTED
    )


def test_unresolved_attempt_projection_is_reported_by_inspect(tmp_path) -> None:
    repo = SqliteResetEventRepository(tmp_path / "reset.sqlite3")
    requested = ResetEvent(
        ResetEventId("request-1"),
        ResetEventType.REDEEM_REQUESTED,
        datetime(2026, 8, 10, 12, tzinfo=UTC),
        ResetEventProvenance.USER_ACTION,
        RedeemRequested(RedeemAttemptId("attempt-1")),
    )
    repo.append(requested)

    assert repo.inspect().unresolved_attempt_count == 1
