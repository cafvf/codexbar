# ADR-007 — Historical usage persistence

Status: accepted
Date: 2026-08-09
Release: v1.3
Requirement: REQ-HISTORY-001
Change taxonomy: ARCH

## Context

v1.3 requires persistent local normalized usage history across process restarts.

The store must support:
- frequent append-like writes;
- atomic snapshot + multiple-window persistence;
- time-range queries;
- stable-window queries;
- 30-day retention/pruning;
- schema/version checks;
- deterministic inspection;
- later analytical workloads without redesigning the storage boundary.

History is application data, not configuration, and must remain isolated from schema-v1 `settings.json`.

## Decision

Use a single local **SQLite** database at the canonical host-user XDG data path:

`$XDG_DATA_HOME/codexbar/history.sqlite3`

fallback:

`$HOME/.local/share/codexbar/history.sqlite3`

The application/history layer depends on a history port. SQLite exists only in infrastructure.

## Alternatives considered

### JSONL

Advantages:
- trivial append;
- human-readable;
- easy initial implementation.

Rejected because:
- time/window queries require scanning;
- pruning requires rewrite/rotation;
- atomic snapshot-with-children semantics are implicit rather than relational;
- schema migration becomes custom file-processing logic;
- later analytics would likely require a second storage/query layer.

### Monolithic JSON

Advantages:
- familiar and similar to settings persistence.

Rejected because:
- repeated writes rewrite a growing file;
- poor incremental durability/performance;
- pruning/query require loading/rebuilding the document;
- unsuitable for potentially hundreds of thousands of observations.

### SQLite

Accepted because:
- transactional;
- local and serverless;
- Python standard-library support;
- explicit schema/constraints;
- indexed time/window queries;
- referential integrity;
- deterministic pruning;
- suitable foundation for future analytics without requiring v1.3 analytics.

## Database schema

Schema version: **1**.

Recommended physical schema:

```sql
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
```

`history_meta` contains at minimum:

`schema_version = 1`

## Timestamp representation

Persist timestamps as canonical UTC ISO-8601 text with a stable formatter.

Requirements:
- input timestamps are timezone-aware;
- convert to UTC before persistence;
- use one canonical representation so lexicographic SQLite ordering equals chronological ordering;
- reconstruct timezone-aware UTC `datetime` objects on read.

The implementation SHALL define and test the exact formatter; precision must preserve current
`UsageSnapshot.observed_at` semantics.

## Decimal representation

Persist `Fraction.value` as canonical decimal text, not binary floating point.

Reason:
- preserves normalized Decimal semantics;
- avoids floating-point drift;
- round-trip reconstruction remains explicit.

## Observation identity and retry idempotency

The store needs protection against accidental duplicate writes of the **same logical refresh result** while
allowing equal values observed at different times.

Use a deterministic `observation_key` derived from normalized snapshot identity fields, including at least:
- canonical `observed_at_utc`;
- normalized source;
- stable normalized window observations.

The exact hash/encoding is an infrastructure implementation detail and SHALL be deterministic.

A repeated write with the same observation key is idempotent.

Two observations at different `observed_at` values are distinct even when all remaining values match.

This key is not a provider/account identifier and must contain/hash normalized domain data only.

## Transactions

Each `append(snapshot)` operation uses one transaction:

1. validate eligibility at the application boundary;
2. begin transaction;
3. insert snapshot identity/metadata;
4. insert all child window observations;
5. commit.

Any failure rolls back the entire snapshot unit.

Foreign keys SHALL be enabled for each SQLite connection.

## Journal/durability policy

Use SQLite's default rollback journal initially.

Do **not** enable WAL in v1.3 without demonstrated concurrency need.

Rationale:
- CodexBar has one application writer;
- history operations are small;
- simpler filesystem behavior;
- fewer auxiliary files;
- no evidence currently justifies WAL complexity.

Use explicit transactions.

Durability PRAGMAs should remain at safe SQLite defaults unless profiling produces a documented reason to
change them.

## Schema handling and migration policy

v1.3 supports history schema version 1 only.

Rules:
- absent database: repository may create schema v1;
- valid schema v1: open normally;
- unknown schema version: fail closed;
- missing required tables/columns or integrity/schema mismatch: treat as history document/storage error;
- do not silently migrate;
- do not silently delete/recreate;
- future schema migration requires a new compatibility decision/ADR update.

## Corruption policy

Opening/querying a corrupt SQLite database must produce a normalized history storage error.

CodexBar SHALL NOT:
- delete it;
- overwrite it;
- automatically recreate over the same path.

Explicit repair/import/export are outside v1.3.

## Retention

Fixed retention: 30 days.

Prune by snapshot UTC observation time:

`DELETE snapshots WHERE observed_at_utc < cutoff_utc`

with child rows removed via `ON DELETE CASCADE`.

Cutoff equality is retained.

Pruning and append may be performed in one maintenance sequence but persistence failure isolation remains
mandatory.

## Query model

Primary queries:
- snapshot interval `[start, end)`;
- per-window interval `[start, end)`;
- inspection summary.

Use indexes; do not load the full database merely to filter in Python.

Ordering:
- `observed_at_utc ASC`;
- `id ASC` as deterministic tie-breaker.

## Clear operation

`history clear` performs a transaction deleting snapshot rows.

It:
- preserves `history_meta` and schema;
- relies on cascading deletion for child rows;
- is idempotent;
- does not unlink the database file;
- does not touch settings.

A corrupt/unsupported database cannot be "cleared" as an implicit repair; clear must fail explicitly.

## XDG path policy

History uses XDG **data**, not configuration.

Resolve:
1. canonical host-user `XDG_DATA_HOME` when valid;
2. otherwise `$HOME/.local/share`.

Snap-scoped values that point inside the user's snap sandbox must fall back to canonical host-user data
location, matching CodexBar's established host-user installation/configuration principle.

## Failure isolation

SQLite errors are normalized to history-specific CodexBar errors at the infrastructure boundary.

The history orchestration path must contain expected history failures so they do not alter:
- successful CURRENT refresh result;
- tray view state;
- alert transition evaluation;
- notification delivery.

History diagnostics may report the error independently.

## Security/privacy

Do not persist:
- Codex credentials;
- raw app-server payload;
- account identifiers;
- arbitrary provider metadata.

Persist only the fields defined by REQ-HISTORY-001.

## Consequences

Positive:
- strong transactional semantics;
- efficient query/retention;
- clean basis for future analytics;
- no external database service;
- no new third-party Python dependency required for SQLite.

Costs:
- introduces a new versioned persistent schema;
- requires corruption/schema compatibility policy;
- requires database-focused tests and migrations policy;
- future packaging must preserve host-user data semantics.

## Follow-up

Implementation tasks are in `docs/tasks/v1.3/TASKS.md`.

A future analytics release may add read-side use cases and indexes, but must not redefine v1.3 observation
semantics.
