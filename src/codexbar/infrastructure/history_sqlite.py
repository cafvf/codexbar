from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoricalWindowSample,
    HistoryInspection,
    HistoryInterval,
    HistoryReadError,
    HistoryRepository,
    HistoryWriteError,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId

_SCHEMA_VERSION = 1


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


class SqliteHistoryRepository(HistoryRepository):
    """Schema-v1 SQLite history repository."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_schema(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS history_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS snapshots (
                        id INTEGER PRIMARY KEY,
                        observed_at_utc TEXT NOT NULL,
                        source TEXT NOT NULL,
                        rate_limit_reached_type TEXT,
                        observation_key TEXT NOT NULL UNIQUE
                    );

                    CREATE TABLE IF NOT EXISTS window_observations (
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

                    CREATE INDEX IF NOT EXISTS idx_snapshots_observed_at
                        ON snapshots(observed_at_utc, id);

                    CREATE INDEX IF NOT EXISTS idx_windows_window_id_snapshot
                        ON window_observations(window_id, snapshot_id);
                    """
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO history_meta(key, value)
                    VALUES ('schema_version', ?)
                    """,
                    (str(_SCHEMA_VERSION),),
                )
        except (OSError, sqlite3.Error) as exc:
            raise HistoryWriteError(f"cannot initialize history database: {exc}") from exc

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
        except (ValueError, sqlite3.Error) as exc:
            raise HistoryWriteError(f"cannot append history snapshot: {exc}") from exc

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
        except (ValueError, sqlite3.Error) as exc:
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
        except (ValueError, sqlite3.Error) as exc:
            raise HistoryReadError(f"cannot query window history: {exc}") from exc

    def prune(self, cutoff: datetime) -> int:
        raise NotImplementedError("TASK-318")

    def inspect(self) -> HistoryInspection:
        raise NotImplementedError("TASK-319")

    def clear(self) -> None:
        raise NotImplementedError("TASK-320")
