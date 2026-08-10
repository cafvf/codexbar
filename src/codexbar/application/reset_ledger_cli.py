from __future__ import annotations

from codexbar.application.reset_ledger import ResetLedgerState
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository


def print_reset_ledger_inspection() -> int:
    inspection = SqliteResetEventRepository.inspect_path(reset_ledger_database_path())
    print(f"Path: {inspection.path}")
    print(f"State: {inspection.state.value}")
    if inspection.schema_version is not None:
        print(f"Schema: {inspection.schema_version}")
    if inspection.event_count is not None:
        print(f"Events: {inspection.event_count}")
    if inspection.oldest_occurred_at is not None:
        print(f"Oldest: {inspection.oldest_occurred_at.isoformat()}")
    if inspection.newest_occurred_at is not None:
        print(f"Newest: {inspection.newest_occurred_at.isoformat()}")
    if inspection.unresolved_attempt_count is not None:
        print(f"Unresolved redeem attempts: {inspection.unresolved_attempt_count}")
    return 2 if inspection.state in {
        ResetLedgerState.UNREADABLE,
        ResetLedgerState.UNSUPPORTED,
    } else 0
