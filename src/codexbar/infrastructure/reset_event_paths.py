from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def reset_ledger_database_path(env: Mapping[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    home = Path(values.get("HOME", str(Path.home()))).expanduser()
    raw = values.get("XDG_DATA_HOME")

    if raw:
        candidate = Path(raw).expanduser()
        data_home = candidate if not _is_snap_scoped(candidate, home) else home / ".local" / "share"
    else:
        data_home = home / ".local" / "share"

    return data_home / "codexbar" / "reset-ledger.sqlite3"


def _is_snap_scoped(path: Path, home: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to((home / "snap").resolve(strict=False))
    except ValueError:
        return False
    return True
