from pathlib import Path

from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path


def test_reset_ledger_path_is_independent_and_xdg_data_scoped() -> None:
    env = {"HOME": "/home/alice", "XDG_DATA_HOME": "/data/alice"}
    path = reset_ledger_database_path(env)

    assert path == Path("/data/alice/codexbar/reset-ledger.sqlite3")
    assert path != history_database_path(env)


def test_snap_scoped_xdg_data_falls_back_to_host_user_data() -> None:
    env = {
        "HOME": "/home/alice",
        "XDG_DATA_HOME": "/home/alice/snap/code/123/.local/share",
    }

    assert reset_ledger_database_path(env) == Path(
        "/home/alice/.local/share/codexbar/reset-ledger.sqlite3"
    )
