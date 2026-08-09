from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from codexbar.application.history import (
    HistoryCorruptionError,
    HistoryReadError,
    HistoryState,
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


def test_inspect_connection_failure_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.OperationalError("cannot open database"),
    )

    with pytest.raises(HistoryReadError, match="cannot inspect"):
        repository.inspect()


def test_inspect_corruption_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.DatabaseError("database disk image is malformed"),
    )

    with pytest.raises(HistoryCorruptionError):
        repository.inspect()


def test_clear_connection_failure_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.OperationalError("readonly database"),
    )

    with pytest.raises(HistoryWriteError, match="cannot clear"):
        repository.clear()


def test_clear_corruption_is_normalized(tmp_path) -> None:
    repository = FailingConnectionRepository(
        tmp_path / "history.sqlite3",
        sqlite3.DatabaseError("database disk image is malformed"),
    )

    with pytest.raises(HistoryCorruptionError):
        repository.clear()


def test_inspect_path_unreadable_state_is_non_throwing(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    path.write_bytes(b"broken")

    result = SqliteHistoryRepository.inspect_path(path)

    assert result.state is HistoryState.UNREADABLE
