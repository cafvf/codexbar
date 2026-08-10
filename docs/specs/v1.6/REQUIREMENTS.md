# CodexBar v1.6 — Initial Requirements

Status: frozen for implementation
Theme: Context

## Requirement conventions

- MUST: release-blocking behavior.
- SHOULD: expected behavior that may be revised with documented rationale.
- MAY: optional behavior.
- Contextual statistics are descriptive unless explicitly stated otherwise.

## REQ-CONTEXT-001 — Current-state contextualization

For every CURRENT usage window with sufficient cycle metadata, CodexBar MUST be
able to contextualize the current remaining quota using eligible historical
observations from the same `UsageWindowId`.

Acceptance direction:

- context is never generated from a different window identity;
- STALE current state does not silently become authoritative;
- absence of eligible context yields an explicit unavailable/insufficient state.

## REQ-CYCLE-001 — Authoritative cycle identity

A contextual cycle MUST be identified by `(UsageWindowId, resets_at)`.

`resets_at` MUST come from an authoritative observation.

CodexBar MUST NOT create a contextual cycle boundary solely because remaining
quota increased.

## REQ-COMPARE-001 — Time-to-reset coordinate

Comparable observations MUST be aligned using time remaining until reset:

    h = resets_at - observed_at

The comparison algorithm MUST NOT require a known nominal cycle duration.

## REQ-COMPARE-002 — One observation per cycle

Each historical cycle MUST contribute at most one observation to a single
contextual query.

This invariant applies regardless of polling frequency.

## REQ-COMPARE-003 — Nearest real observation

Within each eligible historical cycle, the reference observation SHOULD be the
real retained observation minimizing:

    abs(h_historical - h_current)

No interpolated observation may be inserted into the reference set.

## REQ-COMPARE-004 — Hybrid contextual tolerance

A historical cycle MUST be excluded when its nearest retained observation is too
far from the current time-to-reset coordinate.

The v1.6 initial tolerance is:

    delta_h_max(h*) = min(alpha * h*, delta_h_cap)

with:

    alpha = 0.05
    delta_h_cap = 2 hours

A candidate historical observation is eligible only when:

    abs(h_historical - h_current) <= delta_h_max(h_current)

The parameters are deliberately conservative initial heuristics. Their values
MUST be documented and SHOULD be reviewed after sufficient real-cycle coverage
and sampling-cadence evidence accumulate.

## REQ-COVERAGE-001 — Independent-cycle count

Every contextual result MUST expose the number N of independent historical cycles
that contributed to the result.

Snapshot count MUST NOT be presented as equivalent to cycle count.

## REQ-COVERAGE-002 — Insufficient evidence

CodexBar MUST support an explicit `insufficient data` contextual state.

No median, reference band, or strong ranking statement should be shown when
evidence does not satisfy the minimum requirement for that statistic.

## REQ-COVERAGE-003 — Coverage classification

Context MUST classify evidence coverage using these initial v1.6 thresholds:

- 0–2 independent cycles: Insufficient
- 3–4 independent cycles: Sparse
- 5–9 independent cycles: Limited
- 10+ independent cycles: Established

These thresholds MUST be documented as product heuristics, not confidence levels.
They SHOULD be reviewed after sufficient empirical v1.6 usage data accumulate.

## REQ-STATS-001 — Empirical median

When coverage permits, CodexBar MUST calculate the median remaining quota of the
reference set.

The median is an empirical descriptive statistic.

## REQ-STATS-002 — Empirical position

When coverage permits, CodexBar MUST report the position of the current remaining
quota relative to the comparable historical cycles.

The primary user-facing representation SHOULD be count/rank based, for example:

    lower than 8 of 9 comparable cycles

A percentile MAY be shown secondarily.

## REQ-STATS-003 — Coverage-adaptive empirical summary

The contextual statistical presentation MUST adapt to coverage:

- Insufficient: evidence count only plus insufficient-data state;
- Sparse: observed min–max range; factual rank/count MAY be shown;
- Limited: median plus observed min–max range and factual rank/count;
- Established: median plus Q25–Q75 empirical middle-50% band and factual
  rank/count.

The UI MUST NOT call observed ranges or Q25–Q75 bands confidence intervals or
predictive intervals.

## REQ-STATS-004 — No forecasting

Context calculations MUST NOT:

- extrapolate future remaining quota;
- estimate time-to-exhaustion;
- fit a predictive consumption trend;
- emit probability of future exhaustion.

## REQ-HISTORY-001 — 180-day retention

The v1.6 target retention for raw eligible usage history MUST be 180 days.

The release SHOULD preserve the existing history schema if measurements show that
the increased retention is operationally acceptable.

## REQ-HISTORY-002 — Existing history compatibility

Existing schema-v1 historical observations MUST remain readable after the v1.6
retention change.

A retention-policy change MUST NOT require destructive migration.

## REQ-UI-CONTEXT-001 — Separate context surface

Context MUST be visually distinguishable from Current, History, Control/Budget,
and Reset actions.

The UI MUST distinguish:

- current authoritative value;
- historical descriptive reference;
- evidence coverage.

## REQ-UI-CONTEXT-002 — Human-readable interpretation

The primary contextual statement SHOULD be interpretable without statistical
terminology.

Preferred form:

    lower than k of N comparable cycles

rather than presenting only a percentile.

## REQ-SAFETY-001 — No current-state substitution

Historical context MUST NOT replace, synthesize, repair, or fabricate CURRENT
usage state.

## REQ-SAFETY-002 — No control side effects

Context evaluation MUST NOT:

- consume reset credits;
- modify reserve policy;
- alter current account state;
- trigger automatic redemption.

## REQ-REGRESSION-001 — v1.5 compatibility

v1.6 MUST preserve validated v1.5 behavior for:

- current usage;
- history;
- settings;
- notifications;
- reset-credit state;
- Control/Budget;
- manual redeem and recovery;
- native indicator / Qt fallback.


## REQ-PERF-001 — Context query performance

A contextual query over the 180-day target retention SHOULD complete fast enough
to keep the Current Details interaction responsive.

Initial validation targets on the supported development machine:

- repository-only reference-set query: p95 <= 100 ms;
- full application context summary: p95 <= 150 ms;

using a synthetic 180-day dataset representative of configured polling cadence.

These are engineering targets, not user-visible timing guarantees. If the schema-v1
implementation misses them, index/query optimization MUST be attempted before a
history schema migration is proposed.

## REQ-PERF-002 — Retention growth characterization

Before accepting the 180-day retention implementation, the release MUST record:

- retained snapshots/day under the benchmark fixture;
- SQLite size/day;
- projected 180-day database size;
- context-query timing;
- existing History-query timing.

No schema-v2 history migration is authorized solely from theoretical growth.

## REQ-TIE-001 — Deterministic nearest-observation tie

If two real observations in the same historical cycle have equal absolute
time-to-reset mismatch relative to h*, selection MUST be deterministic.

Initial rule:

- choose the observation with the later `observed_at`.

This tie-break does not interpolate or average observations.

## REQ-RANK-001 — Rank semantics

The factual rank/count statement MUST have deterministic tie handling.

For current remaining r* and N reference-cycle values:

- `lower_count` = number of reference values strictly greater than r*;
- `equal_count` = number of reference values equal to r*;
- `higher_count` = number of reference values strictly less than r*.

The UI MAY collapse this to a simple statement when `equal_count == 0`, for
example:

    lower than 8 of 9 comparable cycles

When ties exist, the UI MUST not imply a strict ordering that is false.

## REQ-QUANTILE-001 — Quantile convention

For Established coverage, Q25 and Q75 MUST use one documented deterministic
quantile convention.

Initial v1.6 convention:

- sort the N empirical reference values;
- use linear interpolation between adjacent order statistics at fractional
  index `(N - 1) * p`, for p in {0.25, 0.75}.

The same convention MUST be used in production and tests.

## REQ-TIME-001 — Timezone normalization

All contextual time arithmetic MUST use timezone-aware instants normalized to UTC
at the application/domain boundary.

Equivalent instants in different timezone offsets MUST produce identical h and
cycle selection.

## REQ-CURRENT-CYCLE-001 — Exclude current cycle

The current cycle identified by `(UsageWindowId, current resets_at)` MUST NOT be
counted as an independent historical comparator, even when earlier observations
from that same cycle already exist in the 180-day history.

## REQ-RETENTION-EDGE-001 — Half-open retention boundary

Retention pruning MUST preserve the existing deterministic boundary semantics.

The 180-day retention cutoff MUST be computed from one captured reference instant.
Rows strictly older than the cutoff are pruned; rows at the cutoff remain eligible
unless the existing history contract explicitly specifies otherwise.

## REQ-FAILURE-001 — Context failure isolation

Context repository/read/statistical failures MUST degrade only the Context
surface.

They MUST NOT make Current usage, Control/Budget, reset-credit state, History, or
manual redeem unavailable when those capabilities are otherwise healthy.
