from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from codexbar.application.analytics import (
    AbsentHistoryAnalyticsRepository,
    FailedHistoryAnalyticsRepository,
    HistoryAnalyticsRepository,
)
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoricalWindowSample,
    HistoryCorruptionError,
    HistoryInspection,
    HistoryInterval,
    HistoryReadError,
    HistoryRepository,
    HistorySchemaError,
    HistoryState,
    HistoryWriteError,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId

_SCHEMA_VERSION = 1
_REQUIRED_TABLES = {
    "history_meta": {"key", "value"},
    "snapshots": {
        "id",
        "observed_at_utc",
        "source",
        "rate_limit_reached_type",
        "observation_key",
    },
    "window_observations": {
        "snapshot_id",
        "window_id",
        "label",
        "remaining",
        "resets_at_utc",
    },
}


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("history timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("persisted history timestamp is not timezone-aware")
    return parsed.astimezone(UTC)


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _observation_key(snapshot: HistoricalSnapshot) -> str:
    payload = {
        "observed_at": _format_timestamp(snapshot.observed_at),
        "source": snapshot.source.value,
        "rate_limit_reached_type": snapshot.rate_limit_reached_type,
        "windows": [
            {
                "id": window.window_id.value,
                "label": window.label,
                "remaining": _format_decimal(window.remaining.value),
                "resets_at": (
                    _format_timestamp(window.resets_at)
                    if window.resets_at is not None
                    else None
                ),
            }
            for window in sorted(snapshot.windows, key=lambda item: item.window_id.value)
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _schema_sql() -> str:
    return """
        CREATE TABLE history_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE snapshots (
            id INTEGER PRIMARY KEY,
            observed_at_utc TEXT NOT NULL,
            source TEXT NOT NULL,
            rate_limit_reached_type TEXT,
            observation_key TEXT NOT NULL UNIQUE
        );

        CREATE TABLE window_observations (
            snapshot_id INTEGER NOT NULL,
            window_id TEXT NOT NULL,
            label TEXT NOT NULL,
            remaining TEXT NOT NULL,
            resets_at_utc TEXT,
            PRIMARY KEY (snapshot_id, window_id),
            FOREIGN KEY (snapshot_id)
                REFERENCES snapshots(id)
                ON DELETE CASCADE
        );

        CREATE INDEX idx_snapshots_observed_at
            ON snapshots(observed_at_utc, id);

        CREATE INDEX idx_windows_window_id_snapshot
            ON window_observations(window_id, snapshot_id);
    """


def _is_corruption_error(exc: sqlite3.DatabaseError) -> bool:
    text = str(exc).lower()
    markers = (
        "file is not a database",
        "database disk image is malformed",
        "database corrupt",
        "malformed database schema",
    )
    return any(marker in text for marker in markers)


class SqliteHistoryRepository(HistoryRepository):
    """Schema-v1 SQLite history repository."""

    def __init__(self, path: Path) -> None:
        self._path = path
        if path.exists():
            self._validate_existing_schema()
        else:
            self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_schema(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(_schema_sql())
                connection.execute(
                    """
                    INSERT INTO history_meta(key, value)
                    VALUES ('schema_version', ?)
                    """,
                    (str(_SCHEMA_VERSION),),
                )
        except OSError as exc:
            raise HistoryWriteError(f"cannot create history database: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, operation="create")

    def _validate_existing_schema(self) -> None:
        try:
            with self._connect() as connection:
                version_row = connection.execute(
                    """
                    SELECT value
                    FROM history_meta
                    WHERE key = 'schema_version'
                    """
                ).fetchone()
                if version_row is None:
                    raise HistorySchemaError("history schema version is missing")
                if version_row[0] != str(_SCHEMA_VERSION):
                    raise HistorySchemaError(
                        f"unsupported history schema version: {version_row[0]}"
                    )

                for table, required_columns in _REQUIRED_TABLES.items():
                    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
                    actual_columns = {row[1] for row in rows}
                    if not rows or not required_columns.issubset(actual_columns):
                        raise HistorySchemaError(
                            f"history table {table!r} does not match schema v1"
                        )

                foreign_keys = connection.execute(
                    "PRAGMA foreign_key_list(window_observations)"
                ).fetchall()
                has_snapshot_cascade = any(
                    row[2] == "snapshots"
                    and row[3] == "snapshot_id"
                    and row[6].upper() == "CASCADE"
                    for row in foreign_keys
                )
                if not has_snapshot_cascade:
                    raise HistorySchemaError(
                        "history window_observations cascade constraint is missing"
                    )
        except HistorySchemaError:
            raise
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, operation="validate")

    @staticmethod
    def _raise_database_error(
        exc: sqlite3.DatabaseError,
        *,
        operation: str,
    ) -> None:
        if _is_corruption_error(exc):
            raise HistoryCorruptionError(
                f"history database is corrupt during {operation}: {exc}"
            ) from exc
        raise HistoryReadError(
            f"cannot {operation} history database: {exc}"
        ) from exc

    def append(self, snapshot: HistoricalSnapshot) -> None:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO snapshots(
                        observed_at_utc,
                        source,
                        rate_limit_reached_type,
                        observation_key
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        _format_timestamp(snapshot.observed_at),
                        snapshot.source.value,
                        snapshot.rate_limit_reached_type,
                        _observation_key(snapshot),
                    ),
                )
                if cursor.rowcount == 0:
                    return
                snapshot_id = cursor.lastrowid
                if snapshot_id is None:
                    raise sqlite3.DatabaseError("missing snapshot id after insert")
                connection.executemany(
                    """
                    INSERT INTO window_observations(
                        snapshot_id,
                        window_id,
                        label,
                        remaining,
                        resets_at_utc
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            snapshot_id,
                            window.window_id.value,
                            window.label,
                            _format_decimal(window.remaining.value),
                            (
                                _format_timestamp(window.resets_at)
                                if window.resets_at is not None
                                else None
                            ),
                        )
                        for window in snapshot.windows
                    ],
                )
        except ValueError as exc:
            raise HistoryWriteError(f"cannot append history snapshot: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            if _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during append: {exc}"
                ) from exc
            raise HistoryWriteError(
                f"cannot append history snapshot: {exc}"
            ) from exc

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        try:
            with self._connect() as connection:
                snapshot_rows = connection.execute(
                    """
                    SELECT id, observed_at_utc, source, rate_limit_reached_type
                    FROM snapshots
                    WHERE observed_at_utc >= ? AND observed_at_utc < ?
                    ORDER BY observed_at_utc ASC, id ASC
                    """,
                    (
                        _format_timestamp(interval.start),
                        _format_timestamp(interval.end),
                    ),
                ).fetchall()

                results: list[HistoricalSnapshot] = []
                for snapshot_id, observed_at, source, rate_type in snapshot_rows:
                    window_rows = connection.execute(
                        """
                        SELECT window_id, label, remaining, resets_at_utc
                        FROM window_observations
                        WHERE snapshot_id = ?
                        ORDER BY window_id ASC
                        """,
                        (snapshot_id,),
                    ).fetchall()
                    results.append(
                        HistoricalSnapshot(
                            observed_at=_parse_timestamp(observed_at),
                            source=UsageSource(source),
                            windows=tuple(
                                HistoricalWindowObservation(
                                    window_id=UsageWindowId(window_id),
                                    label=label,
                                    remaining=Fraction(Decimal(remaining)),
                                    resets_at=(
                                        _parse_timestamp(resets_at)
                                        if resets_at is not None
                                        else None
                                    ),
                                )
                                for window_id, label, remaining, resets_at in window_rows
                            ),
                            rate_limit_reached_type=rate_type,
                        )
                    )
                return tuple(results)
        except (ValueError, sqlite3.DatabaseError) as exc:
            if isinstance(exc, sqlite3.DatabaseError) and _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during query: {exc}"
                ) from exc
            raise HistoryReadError(f"cannot query history: {exc}") from exc

    def query_window(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[HistoricalWindowSample, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        s.observed_at_utc,
                        s.source,
                        w.label,
                        w.remaining,
                        w.resets_at_utc
                    FROM window_observations AS w
                    JOIN snapshots AS s ON s.id = w.snapshot_id
                    WHERE
                        w.window_id = ?
                        AND s.observed_at_utc >= ?
                        AND s.observed_at_utc < ?
                    ORDER BY s.observed_at_utc ASC, s.id ASC
                    """,
                    (
                        window_id.value,
                        _format_timestamp(interval.start),
                        _format_timestamp(interval.end),
                    ),
                ).fetchall()
                return tuple(
                    HistoricalWindowSample(
                        observed_at=_parse_timestamp(observed_at),
                        source=UsageSource(source),
                        observation=HistoricalWindowObservation(
                            window_id=window_id,
                            label=label,
                            remaining=Fraction(Decimal(remaining)),
                            resets_at=(
                                _parse_timestamp(resets_at)
                                if resets_at is not None
                                else None
                            ),
                        ),
                    )
                    for observed_at, source, label, remaining, resets_at in rows
                )
        except (ValueError, sqlite3.DatabaseError) as exc:
            if isinstance(exc, sqlite3.DatabaseError) and _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during window query: {exc}"
                ) from exc
            raise HistoryReadError(f"cannot query window history: {exc}") from exc

    def list_window_ids(
        self,
        interval: HistoryInterval,
    ) -> tuple[UsageWindowId, ...]:
        """Return distinct stable window identities observed inside an interval."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT DISTINCT w.window_id
                    FROM window_observations AS w
                    JOIN snapshots AS s ON s.id = w.snapshot_id
                    WHERE
                        s.observed_at_utc >= ?
                        AND s.observed_at_utc < ?
                    ORDER BY w.window_id ASC
                    """,
                    (
                        _format_timestamp(interval.start),
                        _format_timestamp(interval.end),
                    ),
                ).fetchall()
                return tuple(UsageWindowId(row[0]) for row in rows)
        except (ValueError, sqlite3.DatabaseError) as exc:
            if isinstance(exc, sqlite3.DatabaseError) and _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during window discovery: {exc}"
                ) from exc
            raise HistoryReadError(f"cannot discover history windows: {exc}") from exc

    def prune(self, cutoff: datetime) -> int:
        try:
            encoded_cutoff = _format_timestamp(cutoff)
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    DELETE FROM snapshots
                    WHERE observed_at_utc < ?
                    """,
                    (encoded_cutoff,),
                )
                return cursor.rowcount
        except ValueError as exc:
            raise HistoryWriteError(f"cannot prune history: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            if _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during prune: {exc}"
                ) from exc
            raise HistoryWriteError(f"cannot prune history: {exc}") from exc

    @classmethod
    def inspect_path(cls, path: Path) -> HistoryInspection:
        """Inspect a history path without creating, repairing, or mutating it."""

        if not path.exists():
            return HistoryInspection(
                path=str(path),
                state=HistoryState.ABSENT,
            )

        try:
            repository = cls(path)
        except HistorySchemaError as exc:
            return HistoryInspection(
                path=str(path),
                state=HistoryState.UNSUPPORTED,
                diagnostic=str(exc),
            )
        except (HistoryCorruptionError, HistoryReadError, HistoryWriteError) as exc:
            return HistoryInspection(
                path=str(path),
                state=HistoryState.UNREADABLE,
                diagnostic=str(exc),
            )

        return repository.inspect()

    def inspect(self) -> HistoryInspection:
        try:
            with self._connect() as connection:
                version_row = connection.execute(
                    """
                    SELECT value
                    FROM history_meta
                    WHERE key = 'schema_version'
                    """
                ).fetchone()
                if version_row is None:
                    raise HistorySchemaError("history schema version is missing")

                aggregate = connection.execute(
                    """
                    SELECT
                        COUNT(*),
                        MIN(observed_at_utc),
                        MAX(observed_at_utc)
                    FROM snapshots
                    """
                ).fetchone()
                if aggregate is None:
                    raise sqlite3.DatabaseError(
                        "history inspection returned no aggregate row"
                    )

                count, oldest, newest = aggregate
                state = (
                    HistoryState.READY_EMPTY
                    if count == 0
                    else HistoryState.READY_NON_EMPTY
                )
                return HistoryInspection(
                    path=str(self._path),
                    state=state,
                    schema_version=int(version_row[0]),
                    snapshot_count=int(count),
                    oldest_observed_at=(
                        _parse_timestamp(oldest) if oldest is not None else None
                    ),
                    newest_observed_at=(
                        _parse_timestamp(newest) if newest is not None else None
                    ),
                )
        except HistorySchemaError:
            raise
        except (ValueError, sqlite3.DatabaseError) as exc:
            if isinstance(exc, sqlite3.DatabaseError) and _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during inspection: {exc}"
                ) from exc
            raise HistoryReadError(f"cannot inspect history: {exc}") from exc

    def clear(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute("DELETE FROM snapshots")
        except sqlite3.DatabaseError as exc:
            if _is_corruption_error(exc):
                raise HistoryCorruptionError(
                    f"history database is corrupt during clear: {exc}"
                ) from exc
            raise HistoryWriteError(f"cannot clear history: {exc}") from exc


def open_history_analytics_repository(
    path: Path,
) -> HistoryAnalyticsRepository:
    """Open history for analytics without creating or repairing persistent storage."""
    if not path.exists():
        return AbsentHistoryAnalyticsRepository()
    try:
        return SqliteHistoryRepository(path)
    except (HistorySchemaError, HistoryCorruptionError, HistoryReadError) as exc:
        return FailedHistoryAnalyticsRepository(exc)
