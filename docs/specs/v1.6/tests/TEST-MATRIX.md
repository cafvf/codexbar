# CodexBar v1.6 — Requirement/Test Matrix

| Requirement | Primary planned tests |
|---|---|
| REQ-CONTEXT-001 | acceptance current-context; application integration |
| REQ-CYCLE-001 | unit cycle identity; missing reset; no jump inference |
| REQ-COMPARE-001 | unit time-to-reset; timezone equivalence |
| REQ-COMPARE-002 | many-polls-one-cycle test |
| REQ-COMPARE-003 | nearest before/after/tie tests |
| REQ-COMPARE-004 | exact hybrid tolerance boundary tests |
| REQ-COVERAGE-001 | independent-cycle count tests |
| REQ-COVERAGE-002 | N=0..2 acceptance |
| REQ-COVERAGE-003 | boundary N=2/3/4/5/9/10 |
| REQ-STATS-001 | odd/even median |
| REQ-STATS-002 | rank and tie semantics |
| REQ-STATS-003 | adaptive summary per coverage class |
| REQ-STATS-004 | architecture/source invariant: no forecast API |
| REQ-HISTORY-001 | 180-day prune integration |
| REQ-HISTORY-002 | existing schema-v1 fixture regression |
| REQ-UI-CONTEXT-001 | UI structure acceptance |
| REQ-UI-CONTEXT-002 | human-readable rank acceptance |
| REQ-SAFETY-001 | no current-state substitution |
| REQ-SAFETY-002 | no control/redeem side effects |
| REQ-REGRESSION-001 | global v1.5 suite |
| REQ-PERF-001 | 180-day benchmark characterization |
| REQ-PERF-002 | size/query report |
| REQ-TIE-001 | equal-distance deterministic tie |
| REQ-RANK-001 | strict/equal count tests |
| REQ-QUANTILE-001 | fixed Q25/Q75 vector tests |
| REQ-TIME-001 | UTC normalization tests |
| REQ-CURRENT-CYCLE-001 | current-cycle exclusion |
| REQ-RETENTION-EDGE-001 | cutoff boundary integration |
| REQ-FAILURE-001 | injected repository failures |
