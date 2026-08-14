# CodexBar v1.7.0 — Release Traceability

Status: release candidate
Release: 1.7.0 — Diagnose
Baseline: 1.6.0 — Context

## Capability traceability

| Capability | Frozen requirements | Primary implementation / evidence | Status |
|---|---|---|---|
| unified diagnostics | REQ-DIAG-001..007 | diagnostic domain/application/infrastructure, Doctor text/JSON, runtime metrics | validated |
| health semantics | REQ-HEALTH-001..003 | `application/runtime_health.py`, `ui/system_health_viewmodel.py`, separate System Health window | validated |
| single GUI owner | REQ-INSTANCE-001..005 | instance ownership coordinator + local `SHOW_DETAILS` IPC | validated |
| Context revisions/cache | REQ-CONTEXT-RUNTIME-001..006 | Current/History revisions, lean schema-v1 candidate read, revision-aware cache | validated |
| async Context UI | REQ-CONTEXT-RUNTIME-007..009 | `ContextController`, background executor, stale-result rejection | validated |
| async redeem UI | REQ-REDEEM-RUNTIME-001..004 | `RedeemExecutionController`, duplicate prevention, late-result suppression | validated |
| account lineage | REQ-LINEAGE-001..004 | single-account local-history status in Doctor/System Health + documentation | validated |
| upstream source shape | REQ-SOURCE-001..005 | multi-bucket Codex selection with legacy fallback and dynamic windows | validated |
| no-policy Budget | REQ-BUDGET-001..002 | `WindowBudget.headroom=None`, explicit not-applicable presentation | validated |
| native hardening | REQ-NATIVE-001..003 | bounded helper stderr, dynamic guide, Qt fallback | validated |
| deferred reset monitor | REQ-RESET-MONITOR-001 | explicit inactive runtime health state | validated |
| version authority | REQ-VERSION-001..002 | `pyproject.toml` + importlib package metadata + three execution modes | validated locally at 1.7.0 |
| hosted CI | REQ-CI-001..003 | Python 3.12/3.13/3.14 matrix; pytest/Ruff/mypy/compileall | validated on release-prep commit |
| target performance | REQ-PERF-001..006 | Phase A/H characterizers + IPC characterization | validated |
| evidence-gated maintenance | REQ-EVIDENCE-001..004 | explicit retain/change ADR outcomes | validated |
| v1.6 regression | REQ-REGRESSION-001 | full regression suite + physical target session | validated |

## Phase G evidence decisions

The evidence-gated maintenance decisions are closed for v1.7:

- persistent app-server: retain one-shot lifecycle;
- History prune cadence: retain current cadence;
- SQLite journal mode: retain current behavior, no WAL migration;
- Ayatana backend: retain validated helper + Qt fallback;
- canberra warning: non-blocking, no hard dependency;
- property-based testing dependency: not added for v1.7.

## Phase H target evidence

Read-only Doctor validation:

- diagnostics schema version: 1;
- overall health: healthy;
- History: schema 1, 2215 snapshots during the recorded validation;
- reset ledger: schema 1, 16 events, zero unresolved redeem attempts;
- settings/History/reset-ledger hashes unchanged before/after Doctor.

Performance characterization, N=20 unless noted:

- Doctor local p95: 1.516 ms <= 500 ms;
- Context cache hit p95: 0.0047 ms <= 5 ms;
- Context Qt synchronous p95: 0.0408 ms <= 50 ms;
- Context cold p95: 17.383 ms <= 150 ms engineering target;
- second-instance `SHOW_DETAILS` IPC p95: 7.853 ms <= 250 ms.

Physical Ubuntu/GNOME/Wayland validation passed after one System Health UX defect
was corrected and retested. System Health is a read-only auto-updating observer;
Open Details owns authoritative manual Refresh semantics.

A real redeem mutation was not manufactured solely for release validation when no
safe unresolved capability was naturally available; Phase E async/retry evidence
remains authoritative for that allowed capability SKIP.

## Release gate

Before tag:

- validate all version modes at 1.7.0;
- run the frozen global gate;
- push the release-prep commit;
- require hosted Python 3.12/3.13/3.14 and uv-tool mode jobs green;
- verify remote `main` at the release commit;
- create annotated `v1.7.0` only after hosted closure.
