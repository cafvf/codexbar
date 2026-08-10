# REQ-RESET-LEDGER-001 — Reset-credit Event Store and Projection

Status: reviewed draft
Priority: P0
Release: v1.5
Change taxonomy: NEW PERSISTENCE / EVENT STORE / AUDIT

## Requirement

CodexBar SHALL persist an append-only, local, schema-versioned Event Store of meaningful reset-credit
observations and redemption actions.

The Event Store is historical evidence. Current account state SHALL NOT be reconstructed from it.

A Projection/Read Model SHALL derive the minimum historical state required for deduplication, monitoring,
redeem recovery and future analysis.

## Persistence boundary

Canonical path:

`$XDG_DATA_HOME/codexbar/reset-events.sqlite3`

Schema version: `1`.

The database is independent from:
- `history.sqlite3`;
- settings;
- current usage;
- notification transport state.

No automatic retention is required in v1.5.

## Event storage shape

Each persisted event SHALL have, conceptually:

- monotonically increasing persisted `sequence`;
- unique `event_id`;
- `event_type`;
- timezone-aware UTC `observed_at`;
- evidence `provenance`;
- optional opaque `credit_id`;
- optional `redeem_attempt_id`;
- `payload_version`;
- normalized typed payload.

The infrastructure MAY serialize typed payloads as versioned JSON.

It SHALL NOT persist:
- raw app-server payloads;
- tokens/credentials;
- account IDs;
- unbounded arbitrary provider documents.

Persisted `sequence`, not wall-clock timestamp alone, is the authoritative ledger ordering.

## Evidence provenance

At minimum:
- `UPSTREAM_SNAPSHOT`;
- `UPSTREAM_ACTION_RESPONSE`;
- `LOCAL_CLOCK`;
- `LOCAL_ACTION`.

## Normative event taxonomy

### Inventory events

`INVENTORY_BASELINED`
- first authoritative count observed;
- does not claim the credits were granted then.

`INVENTORY_COUNT_CHANGED`
- authoritative count changed;
- stores exact before/after;
- cause remains unclassified.

`INVENTORY_DETAIL_COVERAGE_CHANGED`
- coverage changed among `COUNT_ONLY`, `DETAILS_PARTIAL`, `DETAILS_COMPLETE`.

### Credit-detail events

`CREDIT_DISCOVERED`
- first observation of one opaque detailed ID;
- first observed != granted.

`CREDIT_DETAILS_CHANGED`
- previously known detailed metadata changed.

`CREDIT_REMOVED_FROM_AVAILABLE_SET`
- previously known ID is absent from a later `DETAILS_COMPLETE` inventory;
- means only that it left the fully enumerated available set;
- does not by itself mean expired or redeemed.

`CREDIT_EXPIRY_DEADLINE_PASSED`
- local clock passes a previously known `EXPIRES_AT`;
- does not itself confirm expiry.

No deadline event exists for `DOES_NOT_EXPIRE`.

Absence from COUNT_ONLY/PARTIAL inventories produces no removal event.

### Redemption events

`REDEEM_REQUESTED`
`REDEEM_SUCCEEDED`
`REDEEM_ALREADY_SUCCEEDED`
`REDEEM_NOTHING_TO_RESET`
`REDEEM_NO_CREDIT`
`REDEEM_OUTCOME_UNKNOWN`

`REDEEM_REQUESTED` is durable local intent and SHALL precede the first network side effect.

## Projection / Read Model

At minimum the projection SHALL support:

- last authoritative available count;
- last known detail coverage;
- known credit details by opaque ID;
- whether a known credit left a fully enumerated available set;
- known expiry deadlines already signaled;
- redeem attempts and terminal/non-terminal status;
- enough state to prevent duplicate baseline/discovery/change events after restart.

The projection is historical state, not current inventory.

v1.5 MAY rebuild it from the Event Store at startup. A materialized projection table is not required.

## Idempotent event derivation

Processing the same normalized current inventory repeatedly SHALL not append semantically duplicate events.

Event identity/deduplication SHALL be deterministic enough to survive process restart.

## Inspection and destructive maintenance

v1.5 SHALL expose an inspection capability equivalent in spirit to usage-history inspection, including:
- path;
- schema state/version;
- event count;
- oldest/newest event time;
- count of unresolved redeem attempts when available.

v1.5 SHALL NOT expose general `clear` while unresolved redeem attempts may exist.

A later destructive-maintenance requirement may add guarded clear semantics.

## Use cases

### UC-LEDGER-001 — Baseline

First count observation emits baseline only.

### UC-LEDGER-002 — Partial detail growth

Count stays 4; coverage changes from COUNT_ONLY to DETAILS_PARTIAL and two IDs appear.

Coverage and discovery facts are recorded.

### UC-LEDGER-003 — Fully known removal

A COMPLETE inventory `[A,B]` becomes COMPLETE `[B]`.

Ledger records count change if applicable and `CREDIT_REMOVED_FROM_AVAILABLE_SET(A)`, without assigning cause.

### UC-LEDGER-004 — Partial omission

A previously known A is not present in a later PARTIAL list.

No removal/expiry/redeem event is inferred.

### UC-LEDGER-005 — Deadline passage

Known credit A has `EXPIRES_AT(t)` and local time passes t.

Ledger records deadline passage, not confirmed expiry.

### UC-LEDGER-006 — Restart

Projection rebuild prevents duplicated discovery/baseline events.

## Acceptance criteria

- `AC-LEDGER-001`: Event Store is independent from usage history/settings.
- `AC-LEDGER-002`: schema is versioned and validated before use.
- `AC-LEDGER-003`: corrupt/unsupported store fails closed and is not silently replaced.
- `AC-LEDGER-004`: each append is transactional/atomic.
- `AC-LEDGER-005`: persisted sequence is monotonic and authoritative for event order.
- `AC-LEDGER-006`: event IDs are unique.
- `AC-LEDGER-007`: payload schema/version is explicit.
- `AC-LEDGER-008`: first count emits baseline, not fabricated increase.
- `AC-LEDGER-009`: unchanged repeated inventory emits no duplicate facts.
- `AC-LEDGER-010`: coverage changes are auditable.
- `AC-LEDGER-011`: first detailed ID emits discovery without fabricating grant time.
- `AC-LEDGER-012`: source `granted_at` remains distinct from event `observed_at`.
- `AC-LEDGER-013`: partial/count-only omission emits no removal.
- `AC-LEDGER-014`: COMPLETE omission may emit available-set removal only.
- `AC-LEDGER-015`: available-set removal is not relabeled expired/redeemed without independent evidence.
- `AC-LEDGER-016`: concrete expiry deadline can emit deadline-passed once.
- `AC-LEDGER-017`: non-expiring/unknown-detail credits emit no expiry deadline event.
- `AC-LEDGER-018`: restart/replay preserves deduplication.
- `AC-LEDGER-019`: unresolved redeem attempts are recoverable from projection.
- `AC-LEDGER-020`: Event Store failure is isolated from otherwise valid current usage/reset display.
- `AC-LEDGER-021`: Event Store inability to durably persist redeem intent blocks redeem.
- `AC-LEDGER-022`: ledger projection is never presented as CURRENT reset inventory.
- `AC-LEDGER-023`: inspection works for absent/ready/unreadable/unsupported states.
- `AC-LEDGER-024`: no general clear command is exposed in v1.5.
- `AC-LEDGER-025`: credentials/raw account payloads never cross the persistence boundary.

## Architectural invariant

This is an append-only audit Event Store with projections. CodexBar v1.5 is not event-sourced.

## Implementation mapping

Primary task range: `TASK-520..529`.
Detailed AC-to-task/test mapping: `TRACEABILITY.md`.
