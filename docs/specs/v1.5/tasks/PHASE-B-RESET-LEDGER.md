# Phase B — Reset Event Store and Projection

Goal: create durable evidence/recovery infrastructure before any reset side effect.

## TASK-520 — Reset ledger event model

Implement typed event union, event types, provenance, event ID, sequence-facing record and payload versions.

No SQLite code in domain/application event definitions.

Tests:
`tests/unit/test_reset_events.py`.

## TASK-521 — Reset repository contracts and errors

Define application repository/inspection ports and error taxonomy:
- read/write/schema/corruption;
- inspection state;
- append/query needed for projection.

Tests:
`tests/unit/test_reset_ledger_contract.py`.

## TASK-522 — Canonical reset ledger path

Add XDG data path with the same host-user/Snap-scoped fallback philosophy as history.

Ensure path is independent from history/settings.

Tests:
`tests/unit/test_reset_event_paths.py`.

## TASK-523 — SQLite Event Store schema v1

Implement:
- metadata/schema validation;
- monotonic sequence;
- unique event ID;
- typed/versioned normalized payload;
- atomic append;
- inspect.

Do not store raw provider payload.

Tests:
`tests/unit/test_reset_event_sqlite.py`.

## TASK-524 — Projection fold

Implement rebuildable read model:
- last count;
- last coverage;
- known details;
- known removals;
- signaled deadlines;
- redeem attempt states.

Projection is historical only.

Tests:
`tests/unit/test_reset_projection.py`.

## TASK-525 — Inventory-to-event derivation

Implement deterministic event derivation:
- baseline;
- count change;
- coverage change;
- discovery;
- detail change;
- COMPLETE-only available-set removal;
- no removal on PARTIAL/COUNT_ONLY omission.

Tests:
`tests/unit/test_reset_event_derivation.py`.

## TASK-526 — Ledger processing service

Wire normalized reset-current observations to derivation + atomic append in the worker path.

Ordinary ledger failure:
- does not invalidate current usage/reset display;
- is surfaced diagnostically.

Tests:
`tests/unit/test_reset_ledger_service.py`.

## TASK-527 — Deadline-passed event primitive

Implement idempotent service capability to record a known EXPIRES_AT deadline passing once.
Scheduling it belongs to Phase E.

No event for DOES_NOT_EXPIRE or unknown detail.

Tests:
`tests/unit/test_reset_deadline_events.py`.

## TASK-528 — `reset-ledger inspect`

Add CLI inspection:
- path;
- state;
- schema;
- event count;
- oldest/newest;
- unresolved redeem attempts.

Do not add general clear.

Tests:
`tests/acceptance/test_reset_ledger_cli.py`.

## TASK-529 — Phase B regression gate

Run Gate B.
Freeze Event Store schema v1 before Phase D.
