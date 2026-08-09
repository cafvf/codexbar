from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryCorruptionError,
    HistoryInterval,
    HistorySchemaError,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
CUTOFF = NOW - timedelta(days=30)


def historical_snapshot(
    observed_at: datetime,
    *,
    remaining: str = "0.50",
) -> HistoricalSnapshot:
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=UsageWindowId("weekly"),
                label="Weekly",
                remaining=Fraction(Decimal(remaining)),
                resets_at=observed_at + timedelta(days=1),
            ),
            HistoricalWindowObservation(
                window_id=UsageWindowId("five_hour"),
                label="5 hours",
                remaining=Fraction(Decimal("0.75")),
            ),
        ),
        rate_limit_reached_type="weekly",
    )


def query_all(repository: SqliteHistoryRepository) -> tuple[HistoricalSnapshot, ...]:
    return repository.query(
        HistoryInterval(
            CUTOFF - timedelta(days=2),
            NOW + timedelta(days=1),
        )
    )


def test_ac_history_018_019_020_prune_uses_exact_30_day_boundary(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    old = CUTOFF - timedelta(microseconds=1)
    exact = CUTOFF
    new = CUTOFF + timedelta(microseconds=1)

    repository.append(historical_snapshot(old, remaining="0.60"))
    repository.append(historical_snapshot(exact, remaining="0.50"))
    repository.append(historical_snapshot(new, remaining="0.40"))

    removed = repository.prune(CUTOFF)

    assert removed == 1
    assert [snapshot.observed_at for snapshot in query_all(repository)] == [
        exact,
        new,
    ]


def test_ac_history_021_prune_is_idempotent(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(historical_snapshot(CUTOFF - timedelta(days=1)))

    assert repository.prune(CUTOFF) == 1
    assert repository.prune(CUTOFF) == 0


def test_ac_history_022_prune_cascades_window_rows(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    repository.append(historical_snapshot(CUTOFF - timedelta(days=1)))
    repository.append(historical_snapshot(CUTOFF))

    repository.prune(CUTOFF)

    with sqlite3.connect(path) as connection:
        snapshot_count = connection.execute(
            "SELECT COUNT(*) FROM snapshots"
        ).fetchone()[0]
        window_count = connection.execute(
            "SELECT COUNT(*) FROM window_observations"
        ).fetchone()[0]

    assert snapshot_count == 1
    assert window_count == 2


def test_ac_history_023_prune_does_not_touch_settings_file(tmp_path) -> None:
    settings = tmp_path / "settings.json"
    original = '{"schema_version":1,"notifications_enabled":true}\n'
    settings.write_text(original, encoding="utf-8")
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(historical_snapshot(CUTOFF - timedelta(days=1)))

    repository.prune(CUTOFF)

    assert settings.read_text(encoding="utf-8") == original


def test_ac_history_027_unknown_schema_fails_closed_without_replacement(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    del repository

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE history_meta SET value = '999' WHERE key = 'schema_version'"
        )

    before = path.read_bytes()
    with pytest.raises(HistorySchemaError, match="unsupported"):
        SqliteHistoryRepository(path)
    assert path.read_bytes() == before


def test_ac_history_027_missing_schema_table_fails_closed(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE history_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO history_meta(key, value) VALUES ('schema_version', '1')"
        )

    before = path.read_bytes()
    with pytest.raises(HistorySchemaError, match="snapshots"):
        SqliteHistoryRepository(path)
    assert path.read_bytes() == before


def test_ac_history_028_corrupt_database_is_not_deleted_or_reset(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    payload = b"this is deliberately not sqlite"
    path.write_bytes(payload)

    with pytest.raises(HistoryCorruptionError):
        SqliteHistoryRepository(path)

    assert path.read_bytes() == payload
