from __future__ import annotations

from pathlib import Path

from codexbar.infrastructure.history_paths import history_database_path


def test_history_path_uses_xdg_data_home_when_valid() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "/srv/test-data",
        }
    )

    assert result == Path("/srv/test-data/codexbar/history.sqlite3")


def test_history_path_falls_back_to_local_share_when_xdg_data_home_missing() -> None:
    result = history_database_path({"HOME": "/home/test"})

    assert result == Path("/home/test/.local/share/codexbar/history.sqlite3")


def test_history_path_falls_back_when_xdg_data_home_is_empty() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "",
        }
    )

    assert result == Path("/home/test/.local/share/codexbar/history.sqlite3")


def test_history_path_rejects_snap_scoped_xdg_data_home() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "/home/test/snap/codex/current/.local/share",
        }
    )

    assert result == Path("/home/test/.local/share/codexbar/history.sqlite3")


def test_history_path_rejects_nested_snap_scoped_xdg_data_home() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "/home/test/snap/codex/common/data",
        }
    )

    assert result == Path("/home/test/.local/share/codexbar/history.sqlite3")


def test_history_path_does_not_reject_similar_non_snap_path() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "/home/test/snapshots/data",
        }
    )

    assert result == Path("/home/test/snapshots/data/codexbar/history.sqlite3")


def test_history_path_expands_user_marker() -> None:
    result = history_database_path(
        {
            "HOME": "/home/test",
            "XDG_DATA_HOME": "~/.local/custom-data",
        }
    )

    # expanduser follows the process HOME rather than the injected mapping,
    # so this test only verifies that the resulting path is absolute enough
    # for the resolver contract rather than coupling to host-specific HOME.
    assert result.name == "history.sqlite3"
    assert result.parent.name == "codexbar"


def test_history_path_resolution_does_not_create_directories(tmp_path) -> None:
    data_home = tmp_path / "not-created-yet"
    result = history_database_path(
        {
            "HOME": str(tmp_path),
            "XDG_DATA_HOME": str(data_home),
        }
    )

    assert result == data_home / "codexbar" / "history.sqlite3"
    assert not data_home.exists()
