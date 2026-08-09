from __future__ import annotations

import sqlite3
from pathlib import Path

from codexbar import __main__ as cli
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository


def history_path(home: Path) -> Path:
    return home / ".local" / "share" / "codexbar" / "history.sqlite3"


def test_history_inspect_absent_is_non_destructive(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    path = history_path(tmp_path)

    result = cli.main(["history", "inspect"])

    assert result == 0
    assert "State: absent" in capsys.readouterr().out
    assert not path.exists()


def test_history_inspect_ready_empty_reports_schema_and_count(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    path = history_path(tmp_path)
    SqliteHistoryRepository(path)

    result = cli.main(["history", "inspect"])
    output = capsys.readouterr().out

    assert result == 0
    assert "State: ready_empty" in output
    assert "Schema: 1" in output
    assert "Snapshots: 0" in output


def test_history_clear_absent_succeeds_without_creating_database(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    path = history_path(tmp_path)

    result = cli.main(["history", "clear"])

    assert result == 0
    assert "already empty" in capsys.readouterr().out
    assert not path.exists()


def test_history_clear_valid_database_preserves_schema(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    path = history_path(tmp_path)
    SqliteHistoryRepository(path)

    result = cli.main(["history", "clear"])

    assert result == 0
    assert "Usage history cleared." in capsys.readouterr().out
    with sqlite3.connect(path) as connection:
        version = connection.execute(
            "SELECT value FROM history_meta WHERE key = 'schema_version'"
        ).fetchone()
    assert version == ("1",)


def test_history_clear_unsupported_database_fails_without_replacing_it(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    path = history_path(tmp_path)
    repository = SqliteHistoryRepository(path)
    del repository
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE history_meta SET value = '999' WHERE key = 'schema_version'"
        )
    before = path.read_bytes()

    result = cli.main(["history", "clear"])

    assert result == 2
    assert "cannot clear history" in capsys.readouterr().err
    assert path.read_bytes() == before
