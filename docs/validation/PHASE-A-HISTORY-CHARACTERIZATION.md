# CodexBar v1.6 — Phase A History Characterization

Status: implementation evidence for TASK-614..619
Baseline: schema v1
Retention target: 180 days

## Reproduction

Run from the repository root:

```bash
uv run python scripts/characterize_history_v16.py \
  --output docs/validation/PHASE-A-HISTORY-CHARACTERIZATION.local.md
```

The deterministic fixture uses 180 days of observations, 15-minute polling by default and two
opaque test-window identities. It does not depend on production identities or labels such as
`window_300m`, `window_10080m`, `5h` or `Weekly`.

The script reports:

- snapshots/day and window rows/day;
- SQLite bytes/day and projected 180-day size;
- existing 30-day per-window History-query latency;
- 180-day per-window query latency;
- a candidate Context-oriented query over authoritative `resets_at` rows;
- SQLite `EXPLAIN QUERY PLAN` output for each query shape.

Timing output is characterization evidence only. It is deliberately not used as a hard pytest/CI
latency assertion because host load, filesystem and SQLite build can vary materially.

## Reference characterization

A reference run of the Phase A implementation fixture produced:

- 17,280 snapshots over 180 days;
- 34,560 window rows;
- 96 snapshots/day;
- 7,868,416 SQLite bytes (about 7.9 MB);
- about 43,713 bytes/day;
- 30-day History per-window query median about 5.7 ms;
- 180-day per-window query median about 40.2 ms;
- 180-day Context-candidate query median about 38.4 ms.

The query plans use `idx_snapshots_observed_at` and `idx_windows_window_id_snapshot`. The
Context-candidate ordering uses a temporary B-tree, but the measured reference cost does not by
itself justify a schema or index change in Phase A.

These numbers are reference evidence from the implementation environment, not target-workstation
performance guarantees. Re-run the script locally before the Phase A commit to collect comparable
machine-local evidence.

## Persistence decision

Phase A retains **history schema v1** and its existing indexes. No schema migration, Context store
or speculative additional index is introduced.

The characterization query intentionally exercises the future read shape so that an index can be
added later only if measured target-workstation evidence justifies it. This preserves the frozen
"schema-v1 first" decision and keeps schema evolution evidence-driven.

## Gate interpretation

Phase A is implementation-complete when:

- `HISTORY_RETENTION` is 180 days;
- exact cutoff semantics remain `< cutoff` delete / `== cutoff` retain;
- schema-v1 compatibility remains green;
- the existing History suite remains green;
- the characterization script runs successfully on the target workstation;
- the complete repository gate is green.
