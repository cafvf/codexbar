from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoricalWindowSample,
    HistoryInspection,
    HistoryInterval,
    HistoryRepository,
    HistoryState,
)
from codexbar.application.history_runtime import HISTORY_RETENTION, HistoryService
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

NOW = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)
CUTOFF = NOW - timedelta(days=180)
WINDOW_ID = UsageWindowId("context_primary")


class RecordingRepository(HistoryRepository):
    def __init__(self) -> None:
        self.cutoffs: list[datetime] = []

    def append(self, snapshot: HistoricalSnapshot) -> None:
        pass

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        return ()

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]:
        return ()

    def prune(self, cutoff: datetime) -> int:
        self.cutoffs.append(cutoff)
        return 0

    def inspect(self) -> HistoryInspection:
        return HistoryInspection(path="/tmp/history.sqlite3", state=HistoryState.READY_EMPTY)

    def clear(self) -> None:
        pass


def usage_snapshot(observed_at: datetime = NOW) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                id=WINDOW_ID,
                label="Primary context window",
                remaining=Fraction(Decimal("0.50")),
                resets_at=observed_at + timedelta(hours=6),
            ),
        ),
        observed_at=observed_at,
        source=UsageSource.MOCK,
        freshness=Freshness.CURRENT,
    )


def historical_snapshot(observed_at: datetime, remaining: str) -> HistoricalSnapshot:
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=WINDOW_ID,
                label="Primary context window",
                remaining=Fraction(Decimal(remaining)),
                resets_at=observed_at + timedelta(hours=6),
            ),
        ),
    )


def test_task_610_611_retention_contract_is_exactly_180_days() -> None:
    assert timedelta(days=180) == HISTORY_RETENTION

    repository = RecordingRepository()
    result = HistoryService(repository, clock=lambda: NOW).process(usage_snapshot())

    assert result.captured
    assert repository.cutoffs == [CUTOFF]


def test_task_610_maintenance_captures_clock_once_per_current_snapshot() -> None:
    calls = 0

    def clock() -> datetime:
        nonlocal calls
        calls += 1
        return NOW

    repository = RecordingRepository()
    HistoryService(repository, clock=clock).process(usage_snapshot())

    assert calls == 1
    assert repository.cutoffs == [CUTOFF]


def test_task_611_cutoff_normalizes_equivalent_offset_clock_to_utc() -> None:
    local_clock = NOW.astimezone(timezone(timedelta(hours=-3)))
    repository = RecordingRepository()

    HistoryService(repository, clock=lambda: local_clock).process(usage_snapshot())

    assert repository.cutoffs == [CUTOFF]
    assert repository.cutoffs[0].tzinfo is UTC


def test_task_612_180_day_cutoff_is_half_open_and_cascades(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    old = CUTOFF - timedelta(microseconds=1)
    exact = CUTOFF
    new = CUTOFF + timedelta(microseconds=1)

    repository.append(historical_snapshot(old, "0.60"))
    repository.append(historical_snapshot(exact, "0.50"))
    repository.append(historical_snapshot(new, "0.40"))

    assert repository.prune(CUTOFF) == 1

    interval = HistoryInterval(CUTOFF - timedelta(seconds=1), NOW + timedelta(days=1))
    assert [item.observed_at for item in repository.query(interval)] == [exact, new]

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM window_observations"
        ).fetchone()[0] == 2


def test_task_613_existing_schema_v1_remains_readable_and_unchanged(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    repository.append(historical_snapshot(CUTOFF, "0.50"))

    with sqlite3.connect(path) as connection:
        schema_before = connection.execute(
            "SELECT value FROM history_meta WHERE key = 'schema_version'"
        ).fetchone()[0]
        tables_before = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    reopened = SqliteHistoryRepository(path)
    samples = reopened.query_window(
        WINDOW_ID,
        HistoryInterval(CUTOFF, NOW + timedelta(days=1)),
    )

    with sqlite3.connect(path) as connection:
        schema_after = connection.execute(
            "SELECT value FROM history_meta WHERE key = 'schema_version'"
        ).fetchone()[0]
        tables_after = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert schema_before == schema_after == "1"
    assert tables_before == tables_after
    assert len(samples) == 1
    assert samples[0].observed_at == CUTOFF
