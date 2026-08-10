# CodexBar v1.6 — Traceability

Status: frozen for implementation

## Product -> requirement -> use case -> test

| Product capability | Requirements | Use cases | Test evidence |
|---|---|---|---|
| time-to-reset context | CONTEXT-001, COMPARE-001, TIME-001 | UC-1601 | time tests + app integration |
| authoritative cycles | CYCLE-001, CURRENT-CYCLE-001 | UC-1608, UC-1609 | cycle grouping/exclusion |
| independent-cycle evidence | COMPARE-002, COVERAGE-001 | UC-1601 | many-polls-one-cycle |
| hybrid tolerance | COMPARE-004 | UC-1606 | TV-1601/1602 |
| deterministic nearest sample | COMPARE-003, TIE-001 | UC-1607 | TV-1603/1604 |
| coverage states | COVERAGE-002/003 | UC-1602..1605 | N boundary tests |
| empirical statistics | STATS-001/002/003, RANK-001, QUANTILE-001 | UC-1603..1605, UC-1612 | TV-1605..1607 |
| 180-day retention | HISTORY-001/002, RETENTION-EDGE-001 | UC-1611 | prune/schema regression |
| separate Context UI | UI-CONTEXT-001/002 | UC-1601 | UI acceptance/physical |
| failure isolation | FAILURE-001, SAFETY-001 | UC-1610 | injected failures |
| no forecast/control effects | STATS-004, SAFETY-002 | all | architecture/source invariants |
| performance evidence | PERF-001/002 | UC-1601/1611 | characterization report |

## P0 release criteria

Every item below requires automated evidence before Phase G:

- authoritative cycle identity;
- current-cycle exclusion;
- one observation per independent cycle;
- exact hybrid tolerance boundaries;
- deterministic equal-distance tie;
- all coverage thresholds;
- median/rank/Q25/Q75 semantics;
- schema-v1 compatibility;
- 180-day retention boundary;
- failure isolation;
- no Context-driven redeem/alerts;
- v1.5 regressions.

## P1 release criteria

- performance characterization completed;
- Context UI physical validation;
- wording audit for no predictive claims;
- documentation/release metadata.
