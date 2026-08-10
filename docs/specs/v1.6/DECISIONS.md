# CodexBar v1.6 — Product Decisions

Status: frozen for implementation
Theme: Context

## DEC-1601 — Context coordinate

Decision: ACCEPTED

Use time remaining until reset as the primary coordinate:

    h = resets_at - observed_at

Rationale:

- avoids assuming fixed nominal window duration;
- remains valid when provider quota windows change;
- directly answers "how much remained at roughly this point before reset?".

Rejected for MVP:

- fraction of nominal cycle elapsed;
- time since assumed cycle start;
- fixed 5h / weekly coordinates.

## DEC-1602 — History retention

Decision: ACCEPTED

Increase target history retention from 30 days to 180 days.

Rationale:

- 30 days provides too few independent weekly cycles;
- 180 days permits materially better contextual coverage;
- raw history remains useful for History and Context.

Implementation constraint:

- measure database growth and query cost before deciding on schema evolution;
- prefer retaining schema v1 if practical.

## DEC-1603 — Statistical evidence unit

Decision: ACCEPTED

Independent cycles, not snapshots, are the unit of contextual evidence.

Each historical cycle contributes at most one observation to a contextual query.

Rationale:

- avoids sampling-frequency bias;
- prevents pseudoreplication;
- makes coverage interpretable.

## DEC-1604 — MVP statistics

Decision: ACCEPTED

Initial Context MVP consists of:

- current remaining quota;
- historical median;
- empirical central reference band;
- count/rank position relative to comparable cycles;
- number of comparable independent cycles;
- coverage classification.

Forecasting and model-based prediction remain excluded.

## DEC-1605 — Cycle boundary evidence

Decision: ACCEPTED

Only authoritative `resets_at` values establish cycle identity.

Do not infer cycles from remaining-quota increases in v1.6.

Rationale:

- preserves factual semantics;
- avoids false reset identification;
- separates Context from model-based inference.

## DEC-1606 — Historical matching

Decision: ACCEPTED

For each eligible previous cycle, select the retained observation nearest to the
current time-to-reset coordinate.

No interpolation.

Open parameter:

- contextual maximum mismatch tolerance.

## DEC-1607 — Coverage thresholds

Decision: ACCEPTED

Initial v1.6 thresholds:

- 0–2 cycles: Insufficient
- 3–4 cycles: Sparse
- 5–9 cycles: Limited
- 10+ cycles: Established

These thresholds are product heuristics, not statistical guarantees or confidence
levels.

Review policy:

Reassess the thresholds in a later release once 180-day retention has produced
enough real independent cycles to evaluate empirical coverage.

## DEC-1608 — Coverage-adaptive historical summary

Decision: ACCEPTED

Use an adaptive presentation:

- Insufficient (0–2): no distributional summary;
- Sparse (3–4): observed min–max range;
- Limited (5–9): median + observed min–max range;
- Established (10+): median + Q25–Q75 empirical middle-50% band.

Factual rank/count statements may be shown from Sparse upward.

Rationale:

This avoids presenting unstable quantiles from very small samples while still
exposing useful factual evidence.

All ranges and bands remain explicitly empirical and descriptive.

## DEC-1609 — Contextual mismatch tolerance

Decision: ACCEPTED

Use a hybrid tolerance:

    delta_h_max(h*) = min(alpha * h*, delta_h_cap)

Initial conservative values:

    alpha = 0.05
    delta_h_cap = 2 hours

Examples:

- h* = 100 h -> tolerance = min(5 h, 2 h) = 2 h
- h* = 40 h  -> tolerance = min(2 h, 2 h) = 2 h
- h* = 10 h  -> tolerance = min(0.5 h, 2 h) = 30 min
- h* = 2 h   -> tolerance = min(0.1 h, 2 h) = 6 min

Rationale:

- relative scaling becomes stricter near reset;
- the absolute cap prevents overly broad matching far from reset;
- low initial values favor comparability quality over coverage.

Review policy:

`alpha` and `delta_h_cap` are v1.6 initial heuristics. Reassess them after enough
real data exist to inspect:

- achieved comparable-cycle coverage;
- actual polling cadence;
- exclusion rate by time-to-reset;
- sensitivity of contextual summaries to tolerance.

## DEC-1610 — Persistence strategy

Decision: ACCEPTED

Do not introduce a separate Context database in the initial design.

First attempt to derive Context read-only from the existing history store with
180-day retention.

Reconsider only if measurements show unacceptable:

- database growth;
- query latency;
- lifecycle complexity;
- migration constraints.


## DEC-1611 — Nearest-observation tie-break

Decision: ACCEPTED

If two observations in one cycle are equally near h*, select the later
`observed_at`.

Reason:

- deterministic;
- tends to use the more recently measured state;
- avoids averaging/interpolation.

## DEC-1612 — Quantile convention

Decision: ACCEPTED

Use linear interpolation at fractional index `(N - 1) * p` for Q25/Q75.

This convention must be encoded explicitly rather than delegated to an
implementation-library default that may change.

## DEC-1613 — Current-cycle exclusion

Decision: ACCEPTED

Observations from the same `(UsageWindowId, resets_at)` as the current
observation are excluded from historical comparators.

Reason:

They are repeated measurements of the present cycle, not independent historical
evidence.

## DEC-1614 — Performance-first schema policy

Decision: ACCEPTED

Keep history schema v1 for v1.6 unless measured 180-day fixtures fail the
performance/growth gate after reasonable query/index optimization.

No speculative schema migration.

## DEC-1615 — Context UI placement

Decision: ACCEPTED

Context is integrated into Open Details as a separate `Historical context`
section/panel.

It is not added to:

- tray glance text;
- native indicator label;
- notification payloads;
- History charts by default.

This keeps current glance semantics stable and avoids turning descriptive context
into alert policy.

## DEC-1616 — No Context-driven alerts

Decision: ACCEPTED

v1.6 does not notify because a current position is historically unusual.

Rationale:

Coverage thresholds and empirical bands are descriptive heuristics, not calibrated
risk thresholds. Alerting is deferred until a later product decision.
