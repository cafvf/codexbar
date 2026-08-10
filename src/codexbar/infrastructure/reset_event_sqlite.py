from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from codexbar.application.reset_events import (
    CountChanged,
    CoverageChanged,
    CreditDetailChanged,
    CreditDiscovered,
    CreditRemoved,
    DeadlinePassed,
    InventoryBaseline,
    RedeemAttemptId,
    RedeemRequested,
    RedeemTerminal,
    ResetEvent,
    ResetEventId,
    ResetEventPayload,
    ResetEventProvenance,
    ResetEventType,
    SequencedResetEvent,
)
from codexbar.application.reset_ledger import (
    ResetEventRepository,
    ResetLedgerCorruptionError,
    ResetLedgerInspection,
    ResetLedgerReadError,
    ResetLedgerSchemaError,
    ResetLedgerState,
    ResetLedgerWriteError,
)
from codexbar.application.reset_projection import fold_reset_events
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
)

_SCHEMA_VERSION = 1
_REQUIRED_TABLES = {
    "reset_ledger_meta": {"key", "value"},
    "reset_events": {
        "sequence",
        "event_id",
        "event_type",
        "occurred_at_utc",
        "provenance",
        "payload_version",
        "payload_json",
    },
}


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("reset event timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("persisted reset event timestamp is not timezone-aware")
    return parsed.astimezone(UTC)


def _schema_sql() -> str:
    return """
        CREATE TABLE reset_ledger_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE reset_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL,
            occurred_at_utc TEXT NOT NULL,
            provenance TEXT NOT NULL,
            payload_version INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE INDEX idx_reset_events_occurred_at
            ON reset_events(occurred_at_utc, sequence);
    """


def _is_corruption_error(exc: sqlite3.DatabaseError) -> bool:
    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "file is not a database",
            "database disk image is malformed",
            "database corrupt",
            "malformed database schema",
        )
    )


def _detail_to_data(detail: ResetCreditDetail) -> dict[str, Any]:
    return {
        "credit_id": detail.credit_id.value,
        "reset_type": detail.reset_type,
        "status": detail.status,
        "granted_at": _format_timestamp(detail.granted_at),
        "expiry_kind": detail.expiry.kind.value,
        "expiry_instant": (
            _format_timestamp(detail.expiry.instant)
            if detail.expiry.instant is not None
            else None
        ),
        "title": detail.title,
        "description": detail.description,
    }


def _detail_from_data(data: dict[str, Any]) -> ResetCreditDetail:
    expiry_kind = data["expiry_kind"]
    if expiry_kind == "expires_at":
        expiry = ExpiryKnowledge.expires_at(_parse_timestamp(data["expiry_instant"]))
    elif expiry_kind == "does_not_expire":
        expiry = ExpiryKnowledge.does_not_expire()
    else:
        raise ValueError(f"unsupported persisted expiry kind: {expiry_kind}")

    return ResetCreditDetail(
        credit_id=ResetCreditId(data["credit_id"]),
        reset_type=data["reset_type"],
        status=data["status"],
        granted_at=_parse_timestamp(data["granted_at"]),
        expiry=expiry,
        title=data.get("title"),
        description=data.get("description"),
    )


def _payload_to_data(event: ResetEvent) -> dict[str, Any]:
    payload = event.payload
    if isinstance(payload, InventoryBaseline):
        return {"available_count": payload.available_count, "coverage": payload.coverage.value}
    if isinstance(payload, CountChanged):
        return {"previous_count": payload.previous_count, "current_count": payload.current_count}
    if isinstance(payload, CoverageChanged):
        return {"previous": payload.previous.value, "current": payload.current.value}
    if isinstance(payload, CreditDiscovered):
        return {"detail": _detail_to_data(payload.detail)}
    if isinstance(payload, CreditDetailChanged):
        return {
            "previous": _detail_to_data(payload.previous),
            "current": _detail_to_data(payload.current),
        }
    if isinstance(payload, CreditRemoved):
        return {"credit_id": payload.credit_id.value}
    if isinstance(payload, DeadlinePassed):
        return {
            "credit_id": payload.credit_id.value,
            "deadline": _format_timestamp(payload.deadline),
        }
    if isinstance(payload, RedeemRequested):
        return {
            "attempt_id": payload.attempt_id.value,
            "credit_id": payload.credit_id.value if payload.credit_id else None,
        }
    if isinstance(payload, RedeemTerminal):
        return {"attempt_id": payload.attempt_id.value, "diagnostic": payload.diagnostic}
    raise TypeError(f"unsupported reset event payload: {type(payload)!r}")


def _payload_from_data(
    event_type: ResetEventType,
    data: dict[str, Any],
) -> ResetEventPayload:
    if event_type is ResetEventType.INVENTORY_BASELINE:
        return InventoryBaseline(data["available_count"], DetailCoverage(data["coverage"]))
    if event_type is ResetEventType.COUNT_CHANGED:
        return CountChanged(data["previous_count"], data["current_count"])
    if event_type is ResetEventType.COVERAGE_CHANGED:
        return CoverageChanged(
            DetailCoverage(data["previous"]),
            DetailCoverage(data["current"]),
        )
    if event_type is ResetEventType.CREDIT_DISCOVERED:
        return CreditDiscovered(_detail_from_data(data["detail"]))
    if event_type is ResetEventType.CREDIT_DETAIL_CHANGED:
        return CreditDetailChanged(
            _detail_from_data(data["previous"]),
            _detail_from_data(data["current"]),
        )
    if event_type is ResetEventType.CREDIT_REMOVED:
        return CreditRemoved(ResetCreditId(data["credit_id"]))
    if event_type is ResetEventType.DEADLINE_PASSED:
        return DeadlinePassed(
            ResetCreditId(data["credit_id"]),
            _parse_timestamp(data["deadline"]),
        )
    if event_type is ResetEventType.REDEEM_REQUESTED:
        credit_id = data.get("credit_id")
        return RedeemRequested(
            RedeemAttemptId(data["attempt_id"]),
            ResetCreditId(credit_id) if credit_id is not None else None,
        )
    if event_type in {
        ResetEventType.REDEEM_SUCCEEDED,
        ResetEventType.REDEEM_ALREADY_REDEEMED,
        ResetEventType.REDEEM_REJECTED,
        ResetEventType.REDEEM_OUTCOME_UNKNOWN,
    }:
        return RedeemTerminal(
            RedeemAttemptId(data["attempt_id"]),
            data.get("diagnostic"),
        )
    raise ValueError(f"unsupported reset event type: {event_type}")


class SqliteResetEventRepository(ResetEventRepository):
    def __init__(self, path: Path) -> None:
        self._path = path
        if path.exists():
            self._validate_existing_schema()
        else:
            self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _create_schema(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(_schema_sql())
                connection.execute(
                    "INSERT INTO reset_ledger_meta(key, value) VALUES ('schema_version', ?)",
                    (str(_SCHEMA_VERSION),),
                )
        except OSError as exc:
            raise ResetLedgerWriteError(f"cannot create reset ledger: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, "create", write=True)

    def _validate_existing_schema(self) -> None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT value FROM reset_ledger_meta WHERE key = 'schema_version'"
                ).fetchone()
                if row is None:
                    raise ResetLedgerSchemaError("reset ledger schema version is missing")
                if row[0] != str(_SCHEMA_VERSION):
                    raise ResetLedgerSchemaError(
                        f"unsupported reset ledger schema version: {row[0]}"
                    )
                for table, required in _REQUIRED_TABLES.items():
                    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
                    actual = {item[1] for item in rows}
                    if not rows or not required.issubset(actual):
                        raise ResetLedgerSchemaError(
                            f"reset ledger table {table!r} does not match schema v1"
                        )
        except ResetLedgerSchemaError:
            raise
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, "validate")

    @staticmethod
    def _raise_database_error(
        exc: sqlite3.DatabaseError,
        operation: str,
        *,
        write: bool = False,
    ) -> None:
        if _is_corruption_error(exc):
            raise ResetLedgerCorruptionError(
                f"reset ledger database is corrupt during {operation}: {exc}"
            ) from exc
        error = ResetLedgerWriteError if write else ResetLedgerReadError
        raise error(f"cannot {operation} reset ledger: {exc}") from exc

    def append(self, event: ResetEvent) -> bool:
        return self.append_many((event,)) == 1

    def append_many(self, events: tuple[ResetEvent, ...]) -> int:
        if not events:
            return 0
        try:
            with self._connect() as connection:
                before = connection.total_changes
                for event in events:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO reset_events(
                            event_id, event_type, occurred_at_utc,
                            provenance, payload_version, payload_json
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_id.value,
                            event.event_type.value,
                            _format_timestamp(event.occurred_at),
                            event.provenance.value,
                            event.payload_version,
                            json.dumps(
                                _payload_to_data(event),
                                sort_keys=True,
                                separators=(",", ":"),
                                ensure_ascii=False,
                            ),
                        ),
                    )
                return connection.total_changes - before
        except (TypeError, ValueError) as exc:
            raise ResetLedgerWriteError(f"cannot encode reset event: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, "append", write=True)
        raise AssertionError("unreachable")

    def query_all(self) -> tuple[SequencedResetEvent, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT sequence, event_id, event_type, occurred_at_utc,
                           provenance, payload_version, payload_json
                    FROM reset_events
                    ORDER BY sequence ASC
                    """
                ).fetchall()
        except sqlite3.DatabaseError as exc:
            self._raise_database_error(exc, "read")

        records = []
        try:
            for (
                sequence,
                event_id,
                event_type,
                occurred_at,
                provenance,
                version,
                payload_json,
            ) in rows:
                if version != 1:
                    raise ResetLedgerSchemaError(
                        f"unsupported reset event payload version: {version}"
                    )
                kind = ResetEventType(event_type)
                payload_data = json.loads(payload_json)
                if not isinstance(payload_data, dict):
                    raise ValueError("reset event payload must be an object")
                event = ResetEvent(
                    event_id=ResetEventId(event_id),
                    event_type=kind,
                    occurred_at=_parse_timestamp(occurred_at),
                    provenance=ResetEventProvenance(provenance),
                    payload=_payload_from_data(kind, payload_data),
                    payload_version=version,
                )
                records.append(SequencedResetEvent(sequence, event))
        except ResetLedgerSchemaError:
            raise
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ResetLedgerCorruptionError(
                f"persisted reset event is invalid: {exc}"
            ) from exc
        return tuple(records)

    def inspect(self) -> ResetLedgerInspection:
        return self.inspect_path(self._path)

    @classmethod
    def inspect_path(cls, path: Path) -> ResetLedgerInspection:
        if not path.exists():
            return ResetLedgerInspection(str(path), ResetLedgerState.ABSENT)
        try:
            repository = cls(path)
            records = repository.query_all()
            projection = fold_reset_events(records)
        except ResetLedgerSchemaError:
            return ResetLedgerInspection(
                str(path),
                ResetLedgerState.UNSUPPORTED,
            )
        except (ResetLedgerReadError, ResetLedgerCorruptionError):
            return ResetLedgerInspection(
                str(path),
                ResetLedgerState.UNREADABLE,
            )

        if not records:
            return ResetLedgerInspection(
                str(path),
                ResetLedgerState.READY_EMPTY,
                schema_version=_SCHEMA_VERSION,
                event_count=0,
                unresolved_attempt_count=0,
            )

        return ResetLedgerInspection(
            str(path),
            ResetLedgerState.READY_NON_EMPTY,
            schema_version=_SCHEMA_VERSION,
            event_count=len(records),
            oldest_occurred_at=records[0].event.occurred_at,
            newest_occurred_at=records[-1].event.occurred_at,
            unresolved_attempt_count=len(projection.unresolved_attempt_ids),
        )
