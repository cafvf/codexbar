# REQ-ANALYTICS-001 — Descriptive historical usage analysis

Status: validated — v1.4.0 release candidate
Priority: P0  
Release: v1.4  
Change taxonomy: EVOLUTION

## Requirement

CodexBar SHALL derive deterministic descriptive information from persisted historical observations without
reconstructing unobserved usage, inferring authoritative token consumption, or predicting future usage.

Analysis SHALL consume the existing v1.3 history application boundary and normalized historical values.
It SHALL NOT redefine v1.3 historical observation semantics.

Historical analysis SHALL be read-only.

## Definitions

### Analysis interval

Analysis uses the v1.3 half-open interval:

`[start, end)`

Both timestamps are timezone-aware.

### Historical series

For one stable window `w`, a series is the ordered set of actual persisted samples:

`S_w = {(t_i, r_i, resets_at_i, label_i, source_i)}`

No intermediate observations are synthesized.

### Observed change

For at least two observations:

`observed_change = latest_remaining - first_remaining`

Presentation may express this in percentage points.

This value SHALL NOT be labelled as authoritative consumption.

### Observed increase

For consecutive samples:

`increase_i <=> r_i > r_(i-1)`

An observed increase is a factual property of the samples. It SHALL NOT, by itself, be classified as a
confirmed reset.

### Observed extrema

`observed_min = min(r_i)`  
`observed_max = max(r_i)`

These remain explicitly observational.

### Analytical availability

Historical analysis distinguishes successful analytical results from history-unavailable conditions.

Expected history failures include the existing v1.3 history error taxonomy, including read/corruption and
schema-compatibility failures. Such failures remain secondary to current monitoring.

An absent store and a valid-but-empty store may both yield no analytical samples, but a read path SHALL NOT
create an absent store merely to answer an analytical request.

## Supported periods

The product SHALL support:

- previous 24 hours;
- previous 7 days;
- previous 30 days.

One end instant is captured per analytical request and reused for all calculations in that request.
The selected period is not persisted as a setting.

## Historical window discovery

Analysis SHALL support discovery of stable `UsageWindowId` values observed within an interval.

A window that exists historically but is absent from current usage remains analyzable while retained.

Human-readable labels are attributes, not identity.

Historical window discovery SHALL be supported by the history read boundary without requiring
materialization of every historical snapshot solely to determine distinct stable window identities.

The implementation MAY extend the read-side boundary with a dedicated query. Such an extension SHALL retain
history schema version 1.

## UC-ANALYTICS-001 — Select historical observations

- `AC-ANALYTICS-001`: `observed_at == start` is included.
- `AC-ANALYTICS-002`: `observed_at == end` is excluded.
- `AC-ANALYTICS-003`: samples outside the selected window id are excluded.
- `AC-ANALYTICS-004`: result order is deterministic and chronological.
- `AC-ANALYTICS-005`: an empty interval yields an empty analytical result, not fabricated zeros.
- `AC-ANALYTICS-006`: labels do not determine window identity.

## UC-ANALYTICS-002 — Summarize a historical window

For a non-empty series CodexBar SHALL expose:

- observation count;
- first observation timestamp;
- latest observation timestamp;
- first remaining;
- latest remaining;
- observed minimum;
- observed maximum;
- observed change when defined.

Acceptance criteria:

- `AC-ANALYTICS-007`: count equals selected persisted sample count.
- `AC-ANALYTICS-008`: first values derive from the chronologically first observation.
- `AC-ANALYTICS-009`: latest values derive from the chronologically latest observation.
- `AC-ANALYTICS-010`: minimum is the smallest actually observed remaining value.
- `AC-ANALYTICS-011`: maximum is the largest actually observed remaining value.
- `AC-ANALYTICS-012`: observed change equals `latest - first`.
- `AC-ANALYTICS-013`: observed change may be positive, zero or negative.
- `AC-ANALYTICS-014`: a singleton series has no observed-change value rather than an invented zero.
- `AC-ANALYTICS-015`: an empty series produces an explicit empty-summary state.

## UC-ANALYTICS-003 — Identify observed increases

- `AC-ANALYTICS-016`: `r_i > r_(i-1)` creates one observed-increase event.
- `AC-ANALYTICS-017`: equal consecutive values do not create an increase.
- `AC-ANALYTICS-018`: decreasing values do not create an increase.
- `AC-ANALYTICS-019`: multiple increases are preserved independently.
- `AC-ANALYTICS-020`: an observed increase is not classified as a confirmed reset.
- `AC-ANALYTICS-021`: no synthetic sample is inserted at an increase.

Observed-increase information is analytical metadata. v1.4 does not require a user-facing count of such
events in the summary.

## UC-ANALYTICS-004 — Discover analyzable windows

- `AC-ANALYTICS-022`: every returned window id occurs in at least one persisted sample in the interval.
- `AC-ANALYTICS-023`: repeated observations of one `UsageWindowId` produce one selectable identity.
- `AC-ANALYTICS-024`: a historical-only window remains discoverable when current usage omits it.
- `AC-ANALYTICS-025`: historical label changes do not create new identities.
- `AC-ANALYTICS-026`: no historical windows yields an empty collection.
- `AC-ANALYTICS-026A`: discovering distinct window identities does not require materializing every
  historical snapshot solely for discovery.

## UC-ANALYTICS-005 — Preserve observational semantics

- `AC-ANALYTICS-027`: analytics does not interpolate missing samples.
- `AC-ANALYTICS-028`: analytics does not calculate authoritative token consumption.
- `AC-ANALYTICS-029`: analytics does not produce time-to-exhaustion.
- `AC-ANALYTICS-030`: analytics does not extrapolate future remaining quota.
- `AC-ANALYTICS-031`: analytics does not calculate time spent LOW from sample counts.
- `AC-ANALYTICS-032`: analytics does not present a naïve sample mean as time-average remaining usage.
- `AC-ANALYTICS-033`: refresh cadence does not change definitions of supported summaries.

## UC-ANALYTICS-006 — Isolate analytical failure and read-side effects

- `AC-ANALYTICS-034`: expected failures exposed through the v1.3 history error taxonomy, including
  read/corruption and schema failures, produce an analytical unavailable/error result rather than escaping
  into current monitoring.
- `AC-ANALYTICS-035`: analytical failure does not alter current `UsageSnapshot`.
- `AC-ANALYTICS-036`: analytical failure does not mark CURRENT usage STALE.
- `AC-ANALYTICS-037`: analytical failure does not alter alert evaluation.
- `AC-ANALYTICS-038`: analytical failure does not modify or clear history.
- `AC-ANALYTICS-039`: an analytical read against absent history does not create the history database.
- `AC-ANALYTICS-040`: analytics does not implicitly repair, migrate, clear or replace history.

## Architectural invariants

- `INV-ANALYTICS-001`: analytics imports no Qt/UI implementation.
- `INV-ANALYTICS-002`: analytics contains no direct SQLite calls.
- `INV-ANALYTICS-003`: historical UI performs no analytical calculations owned by the application layer.
- `INV-ANALYTICS-004`: analytics is read-only with respect to history.
- `INV-ANALYTICS-005`: analytics does not reconstruct current usage from history.
- `INV-ANALYTICS-006`: analytics accepts normalized historical values, not raw provider payloads.
- `INV-ANALYTICS-007`: settings schema v1 remains unchanged by analytics.
- `INV-ANALYTICS-008`: history schema remains version 1 for v1.4.
- `INV-ANALYTICS-009`: the read-side path does not instantiate/create absent persistent storage as a
  side effect solely to answer a query.

## Primary test specification

Acceptance: `tests/acceptance/test_req_analytics_001.py`

Required scenarios:

1. exact `[start,end)` boundaries;
2. deterministic summary for `0.82, 0.63, 0.41, 1.00, 0.91`;
3. singleton series;
4. empty series;
5. same id with changing labels;
6. different ids with equal labels;
7. historical-only window discovery;
8. semantic guard against forecast/ETA/token/time-in-state outputs;
9. history-read/corruption failure isolation;
10. unsupported-schema analytical failure;
11. absent history read does not create a database;
12. distinct-window discovery does not require full snapshot materialization solely for discovery.

Unit: `tests/unit/test_history_analytics.py`

Pure tests cover empty/singleton/constant/increasing/decreasing/multiple-increase sequences, Decimal
preservation, timezone validation, ordering, invalid intervals and immutable result models.

Read-side adapter tests:
`tests/unit/test_history_sqlite_analytics_queries.py`

These tests SHALL cover distinct-window discovery, interval filtering, historical labels, empty results,
schema-v1 compatibility, absent-store read behavior, normalized corruption/schema failures and query
behavior needed by analytics.
