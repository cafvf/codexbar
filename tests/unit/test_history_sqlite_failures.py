from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from codexbar.application.history import (
    HistoryCorruptionError,
    HistoryReadError,
    HistoryWriteError,
)
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


class FailingConnectionRepository(SqliteHistoryRepository):
    def __init__(self, path: Path, failure: sqlite3.DatabaseError) -> None:
        self._path = path
        self._failure = failure

    def _connect(self) -> sqlite3.Connection:
        raise self._failure


def test_prune_rejects_naive_cutoff_as_history_write_error(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")

    with pytest.raises(HistoryWriteError, match="timezone-aware"):
        repository.prune(T0.replace(tzinfo=None))


def test_query_connection_failure_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.OperationalError("cannot open"),
    )

    from codexbar.application.history import HistoryInterval

    with pytest.raises(HistoryReadError, match="cannot query"):
        repository.query(HistoryInterval(T0, T0.replace(hour=13)))


def test_prune_connection_failure_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.OperationalError("readonly database"),
    )

    with pytest.raises(HistoryWriteError, match="cannot prune"):
        repository.prune(T0)


def test_corruption_marker_is_normalized_to_corruption_error(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.DatabaseError("database disk image is malformed"),
    )

    with pytest.raises(HistoryCorruptionError):
        repository.prune(T0)
