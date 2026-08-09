# REQ-HISTORY-001 — Persistent local normalized usage history

Status: implementation-ready
Priority: P0
Release: v1.3
Change taxonomy: EVOLUTION

## Requirement

CodexBar SHALL persist a bounded local history of eligible normalized usage snapshots so observations remain
available across process restarts without changing the meaning or availability of current usage.

History SHALL record only normalized domain information and SHALL NOT archive raw provider payloads,
credentials or account identifiers.

## Accepted decisions

1. Retention is fixed at **30 days** for v1.3.
2. Persistence uses **SQLite**, per ADR-007.
3. Time-range queries use **half-open intervals `[start, end)`**.
4. v1.3 includes an explicit destructive **`history clear`** operation.
5. **Every eligible CURRENT snapshot** is persisted; no secondary sampling cadence is introduced.

There are no remaining behavioral decisions blocking TDD.

## Definitions

### Historical snapshot

A persisted representation of one eligible `UsageSnapshot`.

Eligibility requires:
- `Freshness.CURRENT`;
- timezone-aware `observed_at`;
- valid normalized windows under the existing domain model.

STALE is a presentation fallback and SHALL NOT become a historical observation.

### Historical window observation

One normalized `UsageWindow` belonging to a historical snapshot.

Stored fields:
- stable `UsageWindowId`;
- label as observed at that time;
- remaining fraction;
- optional reset timestamp.

Snapshot metadata:
- observed timestamp;
- normalized `UsageSource`;
- optional `rate_limit_reached_type`.

Freshness is not persisted because historical rows are CURRENT by definition.

## Observation semantics

History contains discrete observations only.

For observations at `t1` and `t2`, CodexBar knows only the values actually observed at those instants.

It SHALL NOT:
- interpolate between observations;
- fabricate intermediate samples;
- interpret fractional change as authoritative token count;
- interpret missing history as zero usage or zero remaining.

## Capture semantics

Every eligible CURRENT snapshot completing the existing refresh path SHALL be offered to the history
persistence boundary exactly once by that refresh completion.

A snapshot with multiple windows is persisted atomically:
- all snapshot metadata and all child window observations commit;
- or none commit.

History persistence SHALL NOT alter or wrap the `UsageSnapshot` returned to existing consumers.

## Identity and duplicate semantics

Usage-window identity is the stable `UsageWindowId`.

Human-readable labels are historical attributes, not identity.

The database SHALL have an explicit uniqueness/idempotency policy for historical snapshots, defined by
ADR-007. Retrying the same persistence operation after an ambiguous storage outcome SHALL NOT create
unbounded accidental duplicates.

Normal repeated CURRENT refreshes at distinct observation timestamps are distinct historical observations,
even if their values are identical.

## Query semantics

Range queries use:

`[start, end)`

where both timestamps are timezone-aware.

- start is inclusive;
- end is exclusive;
- results are ordered by `observed_at` ascending;
- equal-time ordering is deterministic by persistent snapshot id;
- queries may optionally filter by stable `UsageWindowId`;
- empty results remain empty and never synthesize zero values.

## Retention

Retention duration is exactly **30 days** in v1.3.

For pruning evaluated at timezone-aware instant `now`:

`cutoff = now_utc - 30 days`

- snapshots with `observed_at < cutoff` are deleted;
- snapshots with `observed_at >= cutoff` are retained;
- child window observations are removed through referential integrity/cascade;
- pruning is idempotent;
- retention is fixed and does not change settings schema v1.

Retention scheduling is an implementation concern, but every implementation SHALL guarantee that a
successful history-maintenance cycle can bring the store into compliance with the 30-day policy.

## Failure policy

History is secondary to current monitoring.

History read/write/prune/clear failure SHALL NOT:
- convert successful provider refresh into `UsageSourceError`;
- mark a CURRENT snapshot stale;
- discard current display;
- prevent alert evaluation/delivery;
- terminate the tray process;
- silently reset/delete corrupt storage.

Expected storage failures are normalized behind the history boundary.

Unknown schema versions and corrupt databases fail closed for history operations.

## History clear

v1.3 SHALL provide an explicit destructive clear operation.

`history clear` SHALL:
- require an explicit CLI command;
- delete all historical snapshots and child observations;
- keep the valid schema/database ready for subsequent writes;
- not delete or mutate `settings.json`;
- not modify current in-memory usage or alert state;
- succeed when history is already empty;
- report failure rather than silently replacing a corrupt/unsupported database.

No interactive confirmation prompt is required because the full command itself is the explicit destructive
intent; documentation SHALL clearly label the operation destructive.

## History inspection

v1.3 SHALL provide non-graphical inspection.

Inspection reports:
- resolved database path;
- database existence;
- readable schema version;
- snapshot count;
- oldest observation time;
- newest observation time;
- state distinguishing absent, ready/empty, ready/non-empty and unreadable/unsupported history.

No charts or analytics are included.

## Use cases and acceptance criteria

### UC-HISTORY-001 — Capture eligible observations
- AC-HISTORY-001: a successfully refreshed CURRENT snapshot persists as one historical snapshot.
- AC-HISTORY-002: all windows from one eligible snapshot persist atomically.
- AC-HISTORY-003: STALE produces no historical write.
- AC-HISTORY-004: refresh failure with no new snapshot produces no historical write.
- AC-HISTORY-005: raw provider payloads, credentials and account identifiers are absent from history ports.
- AC-HISTORY-006: reset timestamps and `rate_limit_reached_type` survive persistence round trip.
- AC-HISTORY-007: identical values at distinct `observed_at` timestamps remain distinct observations.

### UC-HISTORY-002 — Persist across restart
- AC-HISTORY-008: data written by one repository/application instance is queryable by a later instance.
- AC-HISTORY-009: history is independent of in-memory alert/deduplication state.
- AC-HISTORY-010: opening existing history does not itself insert an observation.

### UC-HISTORY-003 — Query deterministically
- AC-HISTORY-011: query results are ordered by `observed_at` ascending.
- AC-HISTORY-012: `observed_at == start` is included.
- AC-HISTORY-013: `observed_at == end` is excluded.
- AC-HISTORY-014: filtering by stable window id returns only that window.
- AC-HISTORY-015: historical labels are returned as observed and are not identity.
- AC-HISTORY-016: empty intervals return an empty result.
- AC-HISTORY-017: naive timestamps are rejected at the history application boundary.

### UC-HISTORY-004 — Apply 30-day retention
- AC-HISTORY-018: snapshots strictly older than `now_utc - 30 days` are pruned.
- AC-HISTORY-019: snapshots exactly at the cutoff are retained.
- AC-HISTORY-020: newer snapshots are retained.
- AC-HISTORY-021: pruning is idempotent.
- AC-HISTORY-022: pruning leaves no orphan window observations.
- AC-HISTORY-023: retention does not mutate settings schema v1.

### UC-HISTORY-005 — Isolate failures
- AC-HISTORY-024: history write failure does not change a successful CURRENT refresh result.
- AC-HISTORY-025: history write/prune failure does not prevent alert processing for the same snapshot.
- AC-HISTORY-026: history read failure affects history query/inspection only.
- AC-HISTORY-027: unknown history schema fails closed without replacing the database.
- AC-HISTORY-028: corrupt history storage is not silently deleted/reset.

### UC-HISTORY-006 — Inspect history
- AC-HISTORY-029: inspection reports resolved path and existence.
- AC-HISTORY-030: inspection reports schema version when readable.
- AC-HISTORY-031: inspection reports count and oldest/newest timestamps for non-empty history.
- AC-HISTORY-032: inspection distinguishes absent, ready-empty, ready-non-empty and unreadable/unsupported.

### UC-HISTORY-007 — Clear history explicitly
- AC-HISTORY-033: `history clear` removes all historical snapshots/window observations.
- AC-HISTORY-034: clear preserves the valid database schema.
- AC-HISTORY-035: clear on empty history succeeds.
- AC-HISTORY-036: clear does not mutate settings.
- AC-HISTORY-037: clear does not alter current in-memory usage/alert state.
- AC-HISTORY-038: corrupt/unsupported storage causes clear to fail explicitly rather than replace storage.

## Architectural invariants

- INV-HISTORY-001: domain imports no SQLite/filesystem/infrastructure modules.
- INV-HISTORY-002: history application logic imports no Qt/UI implementation.
- INV-HISTORY-003: current usage is never reconstructed from history.
- INV-HISTORY-004: STALE is never persisted as a new observation.
- INV-HISTORY-005: settings schema v1 is independent from history schema.
- INV-HISTORY-006: persistence consumes normalized domain values only.
- INV-HISTORY-007: storage failure remains outside provider refresh success/failure contract.
- INV-HISTORY-008: history clear cannot become implicit corruption recovery.

## Traceability rule

Implementation tasks and tests SHALL derive from these ACs. Implementation invariants without user-visible
behavior use `INV-HISTORY-*`.

ADR-007 is normative for persistence architecture but SHALL NOT invent behavior beyond this requirement.
