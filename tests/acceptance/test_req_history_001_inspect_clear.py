from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryCorruptionError,
    HistorySchemaError,
    HistoryState,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def snapshot(observed_at: datetime = T0) -> HistoricalSnapshot:
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=UsageWindowId("weekly"),
                label="Weekly",
                remaining=Fraction(Decimal("0.42")),
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


def test_ac_history_029_inspection_reports_absent_path_without_creating_database(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    result = SqliteHistoryRepository.inspect_path(path)

    assert result.path == str(path)
    assert result.state is HistoryState.ABSENT
    assert result.schema_version is None
    assert result.snapshot_count is None
    assert not path.exists()


def test_ac_history_030_inspection_reports_schema_for_ready_empty_database(
    tmp_path,
) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")

    result = repository.inspect()

    assert result.state is HistoryState.READY_EMPTY
    assert result.schema_version == 1
    assert result.snapshot_count == 0
    assert result.oldest_observed_at is None
    assert result.newest_observed_at is None


def test_ac_history_031_inspection_reports_count_oldest_and_newest(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(snapshot(T0 + timedelta(minutes=2)))
    repository.append(snapshot(T0))
    repository.append(snapshot(T0 + timedelta(minutes=1)))

    result = repository.inspect()

    assert result.state is HistoryState.READY_NON_EMPTY
    assert result.schema_version == 1
    assert result.snapshot_count == 3
    assert result.oldest_observed_at == T0
    assert result.newest_observed_at == T0 + timedelta(minutes=2)


def test_ac_history_032_inspection_distinguishes_unsupported_database(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    del repository

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE history_meta SET value = '999' WHERE key = 'schema_version'"
        )

    before = path.read_bytes()
    result = SqliteHistoryRepository.inspect_path(path)

    assert result.state is HistoryState.UNSUPPORTED
    assert result.schema_version is None
    assert result.diagnostic is not None
    assert "unsupported history schema version" in result.diagnostic
    assert path.read_bytes() == before


def test_ac_history_032_inspection_distinguishes_corrupt_database(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    payload = b"not a sqlite database"
    path.write_bytes(payload)

    result = SqliteHistoryRepository.inspect_path(path)

    assert result.state is HistoryState.UNREADABLE
    assert result.diagnostic is not None
    assert path.read_bytes() == payload


def test_ac_history_033_034_clear_removes_history_but_preserves_schema(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    repository.append(snapshot(T0))
    repository.append(snapshot(T0 + timedelta(minutes=1)))

    repository.clear()

    inspection = repository.inspect()
    assert inspection.state is HistoryState.READY_EMPTY
    assert inspection.schema_version == 1
    assert inspection.snapshot_count == 0

    with sqlite3.connect(path) as connection:
        version = connection.execute(
            "SELECT value FROM history_meta WHERE key = 'schema_version'"
        ).fetchone()
        windows = connection.execute(
            "SELECT COUNT(*) FROM window_observations"
        ).fetchone()

    assert version == ("1",)
    assert windows == (0,)


def test_ac_history_035_clear_is_idempotent_on_empty_history(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")

    repository.clear()
    repository.clear()

    assert repository.inspect().state is HistoryState.READY_EMPTY


def test_ac_history_036_clear_does_not_mutate_settings(tmp_path) -> None:
    settings = tmp_path / "settings.json"
    original = '{"schema_version":1,"notifications_enabled":true}\n'
    settings.write_text(original, encoding="utf-8")
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(snapshot())

    repository.clear()

    assert settings.read_text(encoding="utf-8") == original


def test_ac_history_038_unsupported_store_cannot_be_cleared_as_repair(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    del repository

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE history_meta SET value = '999' WHERE key = 'schema_version'"
        )

    before = path.read_bytes()
    with pytest.raises(HistorySchemaError):
        SqliteHistoryRepository(path)
    assert path.read_bytes() == before


def test_ac_history_038_corrupt_store_cannot_be_cleared_as_repair(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    payload = b"deliberately corrupt"
    path.write_bytes(payload)

    with pytest.raises(HistoryCorruptionError):
        SqliteHistoryRepository(path)

    assert path.read_bytes() == payload
