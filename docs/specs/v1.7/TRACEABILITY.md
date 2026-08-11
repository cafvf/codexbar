# CodexBar v1.7 — Traceability

Status: frozen for implementation

| Capability | Requirements | Use cases | Evidence |
|---|---|---|---|
| unified health | DIAG-001..007, HEALTH-001..003 | UC-1701/1702/1712 | unit + doctor integration |
| safe Doctor | DIAG-002..005 | UC-1701/1712 | mutation guards + JSON tests |
| single instance | INSTANCE-001..005 | UC-1703/1704 | IPC integration + physical |
| Context revisions/cache | CONTEXT-RUNTIME-001..004 | UC-1705/1706 | TV-1705..1707 |
| lean Context query | CONTEXT-RUNTIME-005/006 | UC-1705 | repository integration/perf |
| async Context | CONTEXT-RUNTIME-007/008 | UC-1706 | controller + architecture |
| v1.6 Context semantics | CONTEXT-RUNTIME-009 | UC-1705/1706 | TV-1601..1609 |
| async redeem | REDEEM-RUNTIME-001..004 | UC-1707 | controller + delayed fake + physical |
| lineage honesty | LINEAGE-001..004 | UC-1708 | source/architecture/docs |
| multi-bucket source | SOURCE-001..005 | UC-1710 | TV-1709..1711 |
| Budget no-policy | BUDGET-001/002 | UC-1709 | TV-1708 |
| native diagnostics | NATIVE-001..003 | UC-1711 | helper tests + physical |
| reset monitor inactive | RESET-MONITOR-001 | all | architecture/source invariant |
| version authority | VERSION-001/002 | release | metadata tests |
| CI matrix | CI-001..003 | release | GitHub Actions |
| performance | PERF-001..006 | UC-1703/1705/1706/1712 | characterization |
| evidence gates | EVIDENCE-001..004 | release | decision records |
| v1.6 regression | REGRESSION-001 | all | full global gate |

## P0 automated release criteria

Before Phase H physical validation:

- Doctor typed-model parity;
- Doctor no-mutation/no-secret;
- metric bounds/thresholds;
- single-instance IPC ownership/race/stale recovery;
- Context revision/cache/invalidation;
- obsolete Context result rejection;
- v1.6 Context vectors;
- async redeem controller semantics;
- multi-bucket + legacy source fixtures;
- no-policy Budget semantics;
- native stderr bound;
- source/private-auth architecture guards;
- reset-monitor non-activation;
- version authority;
- Python 3.12/3.13/3.14 CI green;
- full v1.6 regression suite.

## P1 target/physical criteria

- target performance characterization;
- second-launch physical focus;
- Context responsiveness;
- System Health physical lifecycle;
- native/fallback health display;
- redeem physical responsiveness/safety;
- final docs/release metadata.

## Evidence-only outcomes

The following can close with "retain existing behavior":

- persistent app-server;
- prune cadence;
- WAL;
- Ayatana migration;
- canberra dependency;
- property-based testing dependency.

Their characterization/decision record is required; implementation change is not.
