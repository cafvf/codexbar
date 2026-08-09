from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def history_database_path(env: Mapping[str, str] | None = None) -> Path:
    """Resolve the canonical host-user history database path.

    History is application data, so it belongs under XDG_DATA_HOME rather than
    XDG_CONFIG_HOME. Snap-scoped XDG paths are rejected in favor of the
    canonical host-user data directory.
    """

    values = dict(os.environ if env is None else env)
    home = Path(values.get("HOME", str(Path.home()))).expanduser()
    raw = values.get("XDG_DATA_HOME")

    if raw:
        candidate = Path(raw).expanduser()
        data_home = (
            candidate
            if not _is_snap_scoped(candidate, home)
            else home / ".local" / "share"
        )
    else:
        data_home = home / ".local" / "share"

    return data_home / "codexbar" / "history.sqlite3"


def _is_snap_scoped(path: Path, home: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(
            (home / "snap").resolve(strict=False)
        )
    except ValueError:
        return False
    return True
