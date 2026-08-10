from pathlib import Path

from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path


def test_reset_ledger_is_not_history_or_settings_storage() -> None:
    env = {"HOME": "/home/test", "XDG_DATA_HOME": "/data/test"}

    reset_path = reset_ledger_database_path(env)
    history_path = history_database_path(env)

    assert reset_path != history_path
    assert reset_path.name == "reset-ledger.sqlite3"
    assert history_path.name == "history.sqlite3"


def test_reset_event_definitions_have_no_sqlite_dependency() -> None:
    source = Path("src/codexbar/application/reset_events.py").read_text()
    assert "sqlite3" not in source
    assert "codexbar.infrastructure" not in source
