# CodexBar v1.3 Release Specification

Status: validated and release-ready
Release target: v1.3.0
Change taxonomy: EVOLUTION
Theme: Remember

## Goal

Create a bounded, versioned, queryable local history of eligible Codex usage snapshots while preserving the
existing current-usage, stale/error, settings and alert contracts.

## Scoped requirement

- `REQ-HISTORY-001` — persistent local normalized usage history.

## Accepted and implemented release decisions

- persistence engine: SQLite schema v1;
- history location: canonical host-user XDG data location;
- eligibility: every successfully obtained `Freshness.CURRENT` snapshot;
- STALE/provider-error fallback does not create a new historical observation;
- retention: fixed 30 days;
- query intervals: half-open `[start, end)`;
- maintenance: explicit destructive `history clear` command;
- storage independent from schema-v1 settings;
- history failures isolated from current usage and alerts;
- history capture/prune runs in the existing refresh worker path;
- no interpolation, analytics, forecasting or charts in v1.3.

ADR-007 records the as-built storage architecture.

## Product intent

v1.3 is a data-foundation release.

It stores discrete normalized observations. It does not claim continuous monitoring and does not reconstruct
unobserved usage between samples.

## Persistence model

The history database contains:
- `history_meta`;
- snapshot-level records;
- child usage-window observations.

A historical snapshot and all its windows are one atomic persistence unit.

Database path:

`$XDG_DATA_HOME/codexbar/history.sqlite3`

Fallback:

`$HOME/.local/share/codexbar/history.sqlite3`

Snap-scoped `XDG_DATA_HOME` paths under `$HOME/snap/` fall back to the host-user data location.

## Retention

v1.3 retains observations satisfying:

`observed_at >= cutoff`

where:

`cutoff = now_utc - 30 days`

Rows strictly older than cutoff are pruned. Cutoff equality is retained. Child rows are removed through the
foreign-key cascade.

## Query semantics

Time-range queries use half-open intervals `[start, end)`:
- `observed_at == start` is included;
- `observed_at == end` is excluded.

Inputs are timezone-aware; persisted comparison values are canonical UTC text. Per-window queries use stable
`UsageWindowId` identity and preserve the label observed at each sample time.

## Runtime composition

Normal CLI and tray execution wrap the real/mock `UsageProvider` in `HistoryCapturingUsageProvider`.

The wrapper:
1. obtains the provider snapshot;
2. offers CURRENT snapshots to `HistoryService`;
3. performs append + 30-day prune in the refresh worker path;
4. returns the original `UsageSnapshot` unchanged.

Expected history failures are contained. They do not fabricate `UsageSourceError`, stale state or alert
failure. If the history repository cannot be initialized, normal current-usage operation continues with
history disabled for that process.

## Inspection and destructive clear

`codexbar history inspect`:
- does not create an absent database;
- reports resolved path and one of `absent`, `ready_empty`, `ready_non_empty`, `unreadable`, `unsupported`;
- reports schema/count/oldest/newest when available.

`codexbar history clear`:
- is explicit destructive intent for observations;
- preserves valid schema/meta;
- is idempotent;
- treats absent history as already empty;
- does not alter settings or current/alert runtime state;
- refuses corrupt/unsupported storage instead of using clear as repair.

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

- [x] `REQ-HISTORY-001` behavior is specified.
- [x] ADR-007 history persistence architecture accepted before implementation.
- [x] every history AC has automated and/or target evidence appropriate to the criterion.
- [x] `INV-HISTORY-001..008` have automated architecture evidence.
- [x] stale/error paths cannot create new historical observations.
- [x] history failure cannot fabricate usage-source failure or break tray/alerts.
- [x] unknown/corrupt history fails closed without silent destructive reset.
- [x] 30-day retention is deterministic and boundary-tested.
- [x] `[start, end)` query semantics are boundary-tested.
- [x] `history clear` is explicit, idempotent and isolated from settings/current/alerts.
- [x] persistence/query architecture remains independent of Qt/UI.
- [x] SQLite I/O runs outside the GUI polling path.
- [x] v1.0-v1.2 regression guards remain green.
- [x] repository-wide pytest, Ruff, strict mypy and compileall passed.
- [x] target workstation validated restart persistence, XDG path, clear, retention/failure harness and tray
  responsiveness.
- [x] final detailed traceability/release documentation reviewed for TASK-332.
- [x] version metadata advanced atomically from 1.2.0 to 1.3.0.
- [ ] final release gate rerun after metadata/lockfile update.
- [ ] clean release commit and annotated `v1.3.0` tag created/pushed.
