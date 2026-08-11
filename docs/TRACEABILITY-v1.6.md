# CodexBar v1.6.0 — Release Traceability

Status: Phase G candidate
Release: 1.6.0 — Context
Baseline: 1.5.0 — Control

## Capability traceability

| Capability | Frozen requirements | Implementation/evidence |
|---|---|---|
| time-to-reset coordinate | CONTEXT-001, TIME-001 | `domain/context.py`, Context domain tests |
| authoritative cycle identity | CYCLE-001, CURRENT-CYCLE-001 | `CycleIdentity`, current-cycle exclusion tests |
| independent-cycle evidence | COMPARE-002, COVERAGE-001 | one selected real observation/cycle; pseudoreplication regression |
| hybrid tolerance | COMPARE-004 | exact `min(0.05*h*, 2h)` tests and Phase F diagnostics |
| deterministic nearest sample | COMPARE-003, TIE-001 | nearest/tie domain tests |
| adaptive coverage | COVERAGE-002/003 | 0–2 / 3–4 / 5–9 / 10+ boundary tests |
| empirical statistics | STATS-001/002/003, RANK-001, QUANTILE-001 | Decimal median/rank/Q25/Q75 tests |
| 180-day retention | HISTORY-001/002, RETENTION-EDGE-001 | shared retention policy + characterization |
| Context application | FAILURE-001, SAFETY-001 | `HistoricalContextService`, explicit absence states |
| Context UI | UI-CONTEXT-001/002 | separate Historical context surface in Open Details |
| no predictive/control authority | STATS-004, SAFETY-002 | architecture tests; alerts/control/redeem remain independent |
| performance | PERF-001/002 | Phase F 180-day storage/query characterization |
| cross-version integration | protected v1.5 baseline | Integration Hardening/Hygiene + regression suite |

## Phase F target-workstation evidence

- schema v1 retained;
- 180-day fixture: 17,280 snapshots / 34,560 window rows;
- database size: 7,868,416 bytes;
- History 30d p50/p95: 4.006 / 5.587 ms;
- window 180d p50/p95: 27.490 / 34.130 ms;
- Context candidate SQL p50/p95: 23.446 / 27.156 ms;
- production Context p50/p95: 187.852 / 201.475 ms;
- no schema-v2 migration or speculative index justified;
- fault/gap/timezone/pseudoreplication diagnostics: PASS.

Machine-local measurements are characterization evidence, not CI thresholds.

## Phase G closure

Required before tag:

- `uv run python scripts/validate_v1_6.py --real-read --full-gate`;
- physical Open Details/History/Context smoke completed;
- real capabilities unavailable at validation time may be recorded as explicit capability SKIP;
- release metadata and lockfile report version 1.6.0;
- working tree clean after release commit;
- tag `v1.6.0` created only after release closure.
