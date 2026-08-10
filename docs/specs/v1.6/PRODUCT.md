# CodexBar v1.6 — Context

Status: frozen for implementation
Theme: Context
Validated baseline: v1.5.0 — Control

## 1. Product intent

CodexBar v1.6 adds historical context to the authoritative current usage state.

The release should answer:

> How unusual is the current remaining quota when compared with previous
> independent cycles at approximately the same time remaining until reset?

v1.6 is explicitly descriptive and contextual. It is not a forecasting release.

## 2. Product problem

v1.5 can report:

- current remaining quota;
- reset-credit capability;
- per-window reserve policy;
- usable headroom;
- historical observations;
- explicit manual reset control.

Those pieces remain largely separate.

v1.6 should combine current state and historical evidence to explain whether the
current state is typical, high, or low relative to previously observed comparable
cycles.

## 3. Core coordinate

The primary contextual coordinate is time remaining until authoritative reset:

    h = resets_at - observed_at

The product must not assume a fixed nominal window duration such as 5 hours or
7 days.

For the current observation, h* defines the point at which previous cycles are
queried for comparable observations.

## 4. Cycle identity

A contextual cycle is identified by:

    (UsageWindowId, resets_at)

Only an authoritative `resets_at` value may establish cycle identity for v1.6.

CodexBar must not infer a cycle boundary solely from:

- an increase in remaining quota;
- apparent reset-like jumps;
- labels such as "Weekly";
- nominal durations;
- historical patterns.

## 5. Independent-cycle principle

The statistical unit of evidence is an independent cycle, not an individual poll.

For one contextual query, each historical cycle may contribute at most one
observation.

This prevents a frequently sampled cycle from dominating a sparsely sampled
cycle.

## 6. Comparable observation

For current time-to-reset h*, CodexBar selects, from each eligible historical
cycle, the real observation whose time-to-reset is nearest to h*.

No interpolation is performed.

A historical observation is included only when its distance from h* satisfies the
hybrid contextual tolerance:

    delta_h_max(h*) = min(alpha * h*, delta_h_cap)

Initial conservative parameters:

    alpha = 0.05
    delta_h_cap = 2 hours

Therefore a historical observation may differ from the current time-to-reset by
at most 5% of the current time remaining, with an absolute ceiling of 2 hours.

These parameters are v1.6 initial heuristics and MUST be reviewed after enough
real cycles exist to evaluate coverage and sampling cadence.

## 7. MVP contextual statistics

The contextual presentation adapts to coverage:

- Insufficient (0–2): show evidence count and an explicit insufficient-data state;
  do not present a distributional summary.
- Sparse (3–4): show evidence count, observed min–max range, and factual rank/count
  comparison when useful.
- Limited (5–9): show evidence count, median, observed min–max range, and factual
  rank/count comparison.
- Established (10+): show evidence count, median, Q25–Q75 empirical middle-50%
  band, and factual rank/count comparison.

The primary user-facing rank remains a statement such as:

    lower than 8 of 9 comparable cycles

Reference ranges and bands are descriptive empirical history. They are not
confidence intervals and not predictive intervals.

## 8. Coverage

Every contextual result must expose the number of independent cycles supporting
it.

The product must distinguish insufficient/sparse evidence from established
historical context.

The initial v1.6 coverage classes are:

- 0–2 comparable cycles: Insufficient
- 3–4 comparable cycles: Sparse
- 5–9 comparable cycles: Limited
- 10+ comparable cycles: Established

These thresholds are product heuristics rather than statistical confidence
levels. They SHOULD be reviewed in a later release when sufficient empirical
cycle data exist.

## 9. Retention

v1.6 changes the target raw-history retention from 30 days to 180 days.

Rationale:

- a 30-day store provides only about four weekly cycles;
- Context requires repeated independent cycles;
- 180 days permits roughly 25 weekly cycles when observations are available.

The implementation should first determine whether the existing schema-v1 history
store can support the longer retention without a schema migration.

A schema migration is not a product requirement unless measurements demonstrate
that it is necessary.

## 10. User experience

Context should be presented as a distinct conceptual surface from:

- Current usage;
- History;
- Control / Budget;
- Reset actions.

Example:

    Historical context

    At approximately this time before reset:

    Current remaining       28%
    Historical median       46%
    Historical range        37–58%

    Current position
    Lower than 8 of 9 comparable cycles

    Coverage
    9 previous cycles — Limited

The exact labels and visual layout remain open to UX design.

## 11. Product invariants

v1.6 must preserve these truths:

1. Current state remains authoritative and comes from the current account source.
2. Historical context never replaces missing current data.
3. Historical data remain discrete observations.
4. No interpolation is required for the contextual reference set.
5. No cycle boundary is inferred from quota jumps.
6. One cycle contributes at most one observation to one contextual query.
7. Context must expose evidence coverage.
8. Context may return "insufficient data".
9. Context does not alter Control/Budget policy.
10. Context does not trigger reset redemption.
11. Context does not change LOW/EXHAUSTED alert semantics.
12. Context does not assume stable fixed-duration quota windows.

## 12. Explicitly out of scope

v1.6 does not provide:

- time-to-exhaustion;
- future remaining-quota prediction;
- regression-based consumption forecasts;
- slope extrapolation;
- probability of future exhaustion;
- Bayesian forecasting;
- automatic reset-credit redemption;
- inferred reset cycles;
- automatic equivalence between different UsageWindowIds;
- authoritative token-consumption accounting.

These remain candidates for later releases only if accumulated data justify them.

## 13. Success criterion

v1.6 succeeds when a user can inspect a current usage window and understand:

- where they are relative to reset;
- how many previous independent cycles are actually comparable;
- what remaining quota was historically typical at that point;
- whether the current state is unusually high or low;
- when the available evidence is too weak to support that comparison.

No predictive claim is necessary for release success.


## 14. Release-facing terminology

Use these terms consistently in UI and documentation:

- **Historical context** — the full feature/surface.
- **Comparable cycle** — one eligible previous cycle.
- **Coverage** — count/classification of independent comparable cycles.
- **Observed range** — empirical min–max from the final reference set.
- **Middle 50%** — empirical Q25–Q75, shown only for Established coverage.
- **Current position** — factual rank/count relative to comparable cycles.

Avoid these terms in v1.6 user-facing output:

- confidence;
- confidence interval;
- prediction interval;
- forecast;
- expected remaining;
- probability of exhaustion.

## 15. Initial release gate

v1.6 is releasable only when:

- 180-day retention is validated without destructive migration;
- cycle/reference selection is deterministic;
- every coverage class has automated acceptance tests;
- current-cycle exclusion is tested;
- tolerance boundary cases are tested exactly;
- Context failure isolation is demonstrated;
- v1.5 global regressions remain green;
- target GUI validation confirms Context remains distinct from Current,
  History, and Control/Budget;
- no predictive wording is present in production UI.
