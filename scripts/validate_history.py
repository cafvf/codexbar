#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryCorruptionError,
    HistoryInterval,
    HistorySchemaError,
    HistoryWriteError,
)
from codexbar.application.history_runtime import HistoryCapturingUsageProvider, HistoryService
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
CUTOFF = NOW - timedelta(days=30)


def historical_snapshot(observed_at: datetime, remaining: str = "0.50") -> HistoricalSnapshot:
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=UsageWindowId("weekly"),
                label="Weekly",
                remaining=Fraction(Decimal(remaining)),
            ),
            HistoricalWindowObservation(
                window_id=UsageWindowId("five_hour"),
                label="5 hours",
                remaining=Fraction(Decimal("0.75")),
            ),
        ),
    )


def usage_snapshot() -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.50")),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )


class Provider:
    def get_usage(self) -> UsageSnapshot:
        return usage_snapshot()


class FailingAppendRepository:
    def append(self, snapshot: HistoricalSnapshot) -> None:
        raise HistoryWriteError("controlled append failure")

    def query(self, interval: HistoryInterval):
        return ()

    def query_window(self, window_id, interval):
        return ()

    def prune(self, cutoff: datetime) -> int:
        raise AssertionError("prune must not run after append failure")

    def inspect(self):
        raise AssertionError("not used")

    def clear(self) -> None:
        raise AssertionError("not used")


def validate_retention(root: Path) -> None:
    path = root / "retention.sqlite3"
    repository = SqliteHistoryRepository(path)
    old = CUTOFF - timedelta(microseconds=1)
    exact = CUTOFF
    new = CUTOFF + timedelta(microseconds=1)
    repository.append(historical_snapshot(old, "0.60"))
    repository.append(historical_snapshot(exact, "0.50"))
    repository.append(historical_snapshot(new, "0.40"))

    removed = repository.prune(CUTOFF)
    result = repository.query(
        HistoryInterval(CUTOFF - timedelta(seconds=1), NOW + timedelta(days=1))
    )

    assert removed == 1
    assert [item.observed_at for item in result] == [exact, new]

    with sqlite3.connect(path) as connection:
        snapshots = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        windows = connection.execute(
            "SELECT COUNT(*) FROM window_observations"
        ).fetchone()[0]
    assert snapshots == 2
    assert windows == 4
    print("PASS: exact 30-day retention and cascade integrity")


def validate_restart_and_clear(root: Path) -> None:
    path = root / "restart.sqlite3"
    first = SqliteHistoryRepository(path)
    first.append(historical_snapshot(NOW))
    assert first.inspect().snapshot_count == 1

    reopened = SqliteHistoryRepository(path)
    assert reopened.inspect().snapshot_count == 1
    reopened.clear()
    empty = reopened.inspect()
    assert empty.schema_version == 1
    assert empty.snapshot_count == 0
    reopened.clear()
    assert reopened.inspect().snapshot_count == 0
    print("PASS: restart persistence, transactional clear, idempotency, schema preservation")


def validate_schema_failure(root: Path) -> None:
    path = root / "unsupported.sqlite3"
    SqliteHistoryRepository(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE history_meta SET value = '999' WHERE key = 'schema_version'"
        )
    before = path.read_bytes()
    try:
        SqliteHistoryRepository(path)
    except HistorySchemaError:
        pass
    else:
        raise AssertionError("unsupported schema was accepted")
    assert path.read_bytes() == before
    print("PASS: unsupported schema fails closed without replacement")


def validate_corruption(root: Path) -> None:
    path = root / "corrupt.sqlite3"
    payload = b"controlled non-sqlite payload"
    path.write_bytes(payload)
    try:
        SqliteHistoryRepository(path)
    except HistoryCorruptionError:
        pass
    else:
        raise AssertionError("corrupt history was accepted")
    assert path.read_bytes() == payload
    print("PASS: corrupt store fails closed without deletion/reset")


def validate_runtime_failure_isolation() -> None:
    service = HistoryService(FailingAppendRepository(), clock=lambda: NOW)
    wrapped = HistoryCapturingUsageProvider(Provider(), service)

    result = wrapped.get_usage()

    assert result == usage_snapshot()
    assert service.last_result.diagnostic is not None
    print("PASS: history append failure does not replace successful CURRENT usage")


def run_all() -> None:
    with tempfile.TemporaryDirectory(prefix="codexbar-history-validation-") as tmp:
        root = Path(tmp)
        validate_retention(root)
        validate_restart_and_clear(root)
        validate_schema_failure(root)
        validate_corruption(root)
        validate_runtime_failure_isolation()
    print("PASS: all controlled history validation scenarios succeeded.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CodexBar v1.3 history behavior.")
    parser.add_argument("scenario", choices=("all",), default="all", nargs="?")
    parser.parse_args()
    run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
