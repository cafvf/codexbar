# CodexBar v1.7 Phase C — Context Runtime Evidence

Status: Gate C green on target workstation
Tasks: TASK-730..739
Phase B remote closure anchor: `781ca31f274ceb6991464fe7f127e3778eaab0ac`
Phase B implementation anchor: `aacb5c5d28b1ae6a0308d64b5dfbaff9e5599c48`
Frozen specification anchor: `b8c159987339546dff1caa19bdf1ff6107ae0fa7`

## Scope implemented

- explicit monotonic `CurrentRevision` at the latest-authoritative-observation boundary;
- explicit monotonic in-memory `HistoryRevision` for runtime History invalidation;
- no Current revision increment when an older observation is merely marked STALE;
- no History revision increment for STALE input, persisted duplicate append, or zero-row prune/clear;
- History revision increment for effective append, prune, and clear mutations;
- revision-aware Context cache keyed by
  `(CurrentRevision, HistoryRevision, UsageWindowId)`;
- STALE Current bypasses a cache entry from the same authoritative revision;
- cache invalidation when either Current or History revision changes;
- lean schema-v1 SQLite Context projection reading only observation time, remaining,
  reset time and the requested window identity supplied by the query;
- no History schema migration;
- final cycle selection, tolerance, tie-break, coverage, rank and empirical statistics
  remain in the existing domain/application path;
- target-workstation characterization for candidate read, cold Context and cache hit.

No asynchronous Context orchestration is included. That remains Phase D.

## Revision rules

### Current

`CurrentRevision` starts at zero for a fresh runtime and advances exactly once after
an authoritative account observation is successfully adopted by
`LatestAccountObservationReader`.

If an upstream read fails and the previous Current snapshot is exposed as STALE, the
revision does not advance. The stale presentation is not a new authoritative Current
generation.

### History

`HistoryRevision` is runtime-only and starts at zero. It advances only after a
read-visible History mutation actually changes persisted state.

The History repository mutation contract exposes that effect directly:

- `append(snapshot) -> bool`: `True` only when a new snapshot is inserted; duplicate
  `INSERT OR IGNORE` returns `False`;
- `prune(cutoff) -> int`: revision advances only when one or more rows are removed;
- `clear() -> int`: revision advances only when one or more snapshots are removed.

STALE input is not offered as a History mutation. Failed writes do not advance the
revision.

This preserves `INV-HISTORY-003`: Current capture does not query or inspect History to
determine mutation effects. In particular, `HistoryService` does not call `query`,
`query_window`, or `inspect` on the History repository in the Current capture path.

## Context cache semantics

The cache stores `HistoricalContextResult`, not Qt state. Production presentation
supplies both Current and History revisions. Legacy/unit callers that omit revision
identity continue through the uncached v1.6-compatible evaluation path.

Only one revision pair is retained at a time; changing either revision clears old
entries. Within one pair each dynamic `UsageWindowId` has an independent entry.

STALE Current bypasses revision caching because stale fallback deliberately retains
the previous authoritative Current revision.

## Lean schema-v1 projection

`SqliteContextHistoryRepository` no longer materializes
`HistoricalWindowSample`/`HistoricalWindowObservation` through the generic History
window query. It executes a read-only schema-v1 join selecting only:

- `snapshots.observed_at_utc`;
- `window_observations.remaining`;
- `window_observations.resets_at_utc`.

The SQL filters only by requested window and half-open time interval, then preserves
chronological ordering. It performs no grouping, ranking, tolerance, cycle selection,
aggregation or quantile/statistical operation.

History remains schema v1. No Context/History schema-v2 file, DDL migration, or schema
upgrade is introduced by Phase C.

## Phase A comparison baseline

The target-workstation Phase A evidence recorded:

| Path | p50 (ms) | p95 (ms) |
|---|---:|---:|
| Context candidate read | 12.162 | 14.502 |
| Context cold | 20.124 | 21.328 |
| repeated v1.6 Context behavior | 24.953 | 27.211 |

These values are the before reference and were measured against the live History store
available during Phase A.

## Phase C target-workstation characterization

Recorded on 2026-08-11 with 2,190 retained History snapshots and N=20 samples.
The characterized dynamic window was `window_10080m`.

| Path | N | p50 (ms) | p95 (ms) | min (ms) | max (ms) |
|---|---:|---:|---:|---:|---:|
| Context candidate read | 20 | 7.510 | 9.530 | 7.183 | 9.873 |
| Context cold | 20 | 15.399 | 17.462 | 15.089 | 17.872 |
| Context cache hit | 20 | 0.005 | 0.007 | 0.004 | 0.007 |

Semantic equivalence between the cold result and the revision-identical cached result:
**PASS**.

Cache-hit release budget (`p95 <= 5 ms`): **PASS**. The measured p95 was `0.007 ms`,
well below the frozen target-workstation budget.

The live History population differed from the Phase A characterization, so candidate
and cold before/after values are recorded as performance evidence rather than treated
as controlled benchmark ratios. The cache-hit path is the new Phase C fast path with
an explicit release budget.

## Regression and gate evidence

Focused revision/cache/lean-projection/architecture validation after the History
mutation-effect correction:

- `29 passed in 0.15s`.

Complete Context-named regression set, including frozen v1.6 Context tests:

- `79 passed in 0.26s`.

Final global gate on the target workstation:

- pytest: `665 passed in 2.96s`;
- Ruff: all checks passed;
- strict mypy: success, no issues in 80 source files;
- compileall: passed;
- `git diff --check`: passed.

The previously existing `INV-HISTORY-003` acceptance invariant also passes after
removing the transient `HistoryService -> repository.inspect()` dependency.

## Gate C closure

Gate C is **GREEN on the target workstation**.

Final evidence:

1. TASK-730 Current revision rules: green;
2. TASK-731 History revision rules: green;
3. TASK-732 exact advancement/no-op tests: green;
4. TASK-733 revision-aware Context cache/invalidation: green;
5. TASK-734 lean schema-v1 Context projection: green;
6. TASK-735 SQL/domain semantic-boundary architecture checks: green;
7. TASK-736 frozen v1.6 Context canonical/regression tests: green;
8. TASK-737 target characterization with N=20: recorded;
9. TASK-738 cache-hit p95 `0.007 ms <= 5 ms`: PASS;
10. TASK-739 before/after and semantic-equivalence evidence: recorded;
11. no History schema migration;
12. global gate: green.

The Phase C implementation therefore satisfies TASK-730..739 and the frozen Gate C
validation requirements. It is ready for staging and commit.
