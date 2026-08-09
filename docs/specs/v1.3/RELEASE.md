# CodexBar v1.3 Release Specification

Status: implementation-ready
Release target: v1.3.0
Change taxonomy: EVOLUTION
Theme: Remember

## Goal

Create a bounded, versioned, queryable local history of eligible Codex usage snapshots while preserving the
existing current-usage, stale/error, settings and alert contracts.

## Scoped requirement

- `REQ-HISTORY-001` — persistent local normalized usage history.

## Accepted release decisions

- persistence engine: SQLite;
- history location: canonical host-user XDG data location;
- eligibility: every successfully refreshed `Freshness.CURRENT` snapshot;
- STALE snapshots are never persisted as new observations;
- retention: fixed 30 days in v1.3;
- query intervals: half-open `[start, end)`;
- maintenance: explicit destructive `history clear` command;
- storage is independent from schema-v1 settings;
- history failures are isolated from current usage and alerts;
- no interpolation, analytics, forecasting or charts in v1.3.

ADR-007 records the storage architecture.

## Product intent

v1.3 is a data-foundation release.

It stores discrete normalized observations. It does not claim continuous monitoring and does not reconstruct
unobserved usage between samples.

## Persistence model

The history database SHALL contain:
- schema metadata;
- snapshot-level records;
- child usage-window observations.

A historical snapshot and all its windows are one atomic persistence unit.

The database path is:

`$XDG_DATA_HOME/codexbar/history.sqlite3`

or, when `XDG_DATA_HOME` is absent:

`$HOME/.local/share/codexbar/history.sqlite3`

Snap-scoped host-path protection SHALL follow the same host-user principle already established for CodexBar
desktop/configuration paths.

## Retention

v1.3 retains observations with:

`observed_at >= cutoff`

where:

`cutoff = now_utc - 30 days`

Rows strictly older than the cutoff are pruned.

Retention operates on snapshots and cascades to child window observations.

## Query semantics

Time-range queries use half-open intervals:

`[start, end)`

Therefore:
- `observed_at == start` is included;
- `observed_at == end` is excluded.

Inputs must be timezone-aware and comparisons use canonical UTC representation.

## Destructive clear semantics

`history clear` is explicit user intent.

It SHALL:
- delete historical snapshot/window rows;
- preserve the database schema;
- preserve settings;
- preserve current runtime state;
- be idempotent;
- not silently run as corruption recovery.

A successful clear on an already-empty database is still success.

## Non-goals

- usage-rate analytics;
- historical graphs/dashboard;
- forecasting;
- exhaustion prediction;
- raw provider archival;
- cloud sync;
- remote database;
- configurable retention;
- reconstructing missing observations;
- changing current usage or alert semantics.

## Release gates

- [ ] `REQ-HISTORY-001` is fully traceable.
- [x] ADR-007 history persistence architecture is accepted before implementation.
- [ ] every history AC has automated evidence.
- [ ] stale/error paths cannot create historical observations.
- [ ] history failure cannot fabricate usage-source failure or break tray/alerts.
- [ ] unknown/corrupt history schema fails closed without silent destructive reset.
- [ ] 30-day retention is deterministic and boundary-tested.
- [ ] `[start, end)` query semantics are boundary-tested.
- [ ] `history clear` is explicit, idempotent and does not alter settings/current usage.
- [ ] persistence/query architecture remains independent of Qt/UI.
- [ ] v1.0-v1.2 suites remain green.
- [ ] repository-wide pytest, ruff, strict mypy and compileall pass.
- [ ] target workstation validates restart persistence, retention, clear and failure isolation.
