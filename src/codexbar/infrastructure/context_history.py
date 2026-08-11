from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from codexbar.application.context import ContextHistoryRepository
from codexbar.application.history import HistoryInterval, HistoryReadError
from codexbar.domain.context import ContextObservation
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

CONTEXT_CANDIDATE_SQL = """
    SELECT
        s.observed_at_utc,
        w.remaining,
        w.resets_at_utc
    FROM window_observations AS w
    JOIN snapshots AS s ON s.id = w.snapshot_id
    WHERE
        w.window_id = ?
        AND s.observed_at_utc >= ?
        AND s.observed_at_utc < ?
    ORDER BY s.observed_at_utc ASC, s.id ASC
"""


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("context history timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("persisted context timestamp is not timezone-aware")
    return parsed.astimezone(UTC)


class SqliteContextHistoryRepository(ContextHistoryRepository):
    """Lean schema-v1 adapter exposing only columns required by Context."""

    def __init__(self, history_repository: SqliteHistoryRepository) -> None:
        self._path = Path(history_repository.inspect().path)
        self._database_uri = self._path.resolve().as_uri() + "?mode=ro"

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        try:
            with sqlite3.connect(self._database_uri, uri=True) as connection:
                rows = connection.execute(
                    CONTEXT_CANDIDATE_SQL,
                    (
                        window_id.value,
                        _format_timestamp(interval.start),
                        _format_timestamp(interval.end),
                    ),
                ).fetchall()
            return tuple(
                ContextObservation(
                    window_id=window_id,
                    observed_at=_parse_timestamp(observed_at),
                    remaining=Fraction(Decimal(remaining)),
                    resets_at=(
                        _parse_timestamp(resets_at)
                        if resets_at is not None
                        else None
                    ),
                )
                for observed_at, remaining, resets_at in rows
            )
        except (ValueError, sqlite3.DatabaseError) as exc:
            raise HistoryReadError(f"cannot query Context candidates: {exc}") from exc
