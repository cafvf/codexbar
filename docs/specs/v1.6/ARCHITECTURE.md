# CodexBar v1.6 — Context Architecture Baseline

Status: frozen for implementation
No implementation tasks are authorized by this document.

## 1. Read path

    CurrentAccountObservation
             |
             v
       current window
    (window_id, remaining,
     observed_at, resets_at)
             |
             v
    Context coordinate h*
             |
             v
    Historical Context Query
             |
             v
    group by historical cycle
    (window_id, resets_at)
             |
             v
    choose nearest retained
    real observation per cycle
             |
             v
    apply hybrid tolerance
    min(0.05*h*, 2 hours)
             |
             v
       ReferenceSet
       one item/cycle
             |
        +----+----+
        |         |
        v         v
     Coverage   Empirical
                statistics
        |         |
        +----+----+
             v
       ContextViewState

## 2. Layering

### Domain

Potential value objects:

- `CycleIdentity`
- `TimeToReset`
- `ComparableCycleObservation`
- `ContextReferenceSet`
- `ContextCoverage`

Domain logic must not depend on Qt or SQLite.

### Application

Potential services:

- `HistoricalContextService`
- `CycleReferenceSelector`
- `ContextSummaryService`

Responsibilities:

- query historical candidates;
- group observations by authoritative cycle;
- select one real observation per cycle;
- apply tolerance;
- calculate empirical summaries;
- return explicit insufficient/unavailable states.

### Infrastructure

Initial strategy:

Reuse schema-v1 history persistence.

Likely new repository query capabilities may be added, but persistence format
should remain unchanged unless measurement proves a migration necessary.

### UI

Potential new surface:

`HistoricalContextPanel`

It should consume an application/presentation view state and must not access
SQLite directly.

## 3. Failure and absence states

Context must distinguish at least:

- current window has no authoritative reset timestamp;
- no historical observations;
- historical observations exist but no identifiable cycles;
- cycles exist but none satisfy time-position tolerance;
- too few comparable cycles for statistics;
- sufficient context;
- history repository unavailable/corrupt.

These states must not convert CURRENT usage into an error.

## 4. Performance concern

180-day retention increases raw rows by approximately 6x relative to the v1.5
30-day policy under similar polling behavior.

Before final architecture:

- measure current DB size per retained day;
- estimate 180-day size;
- benchmark relevant cycle-grouping query;
- benchmark startup/History behavior;
- decide whether indexes are sufficient.

This measurement should occur before any schema-v2 history proposal.

## 5. Statistical invariants

1. No future observation enters the historical reference set.
2. One cycle contributes at most one value.
3. Current cycle is not used as an independent historical comparator.
4. No interpolation is required.
5. Missing reset metadata causes contextual exclusion, not inference.
6. Median/rank/reference band are computed only from the final reference set.
7. Coverage is based on final independent cycle count.
8. The initial mismatch tolerance is `min(0.05*h*, 2 hours)`.
9. Coverage thresholds are 0–2 / 3–4 / 5–9 / 10+ cycles.
10. Statistical presentation adapts to the coverage class.
