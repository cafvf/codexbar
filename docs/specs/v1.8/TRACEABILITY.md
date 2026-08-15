# CodexBar v1.8 — Traceability

Status: frozen for implementation

| Capability | Requirement | Use cases | Acceptance | Primary evidence |
|---|---|---|---|---|
| checkpoint policy | REQ-PLAN-001 | UC-1801/1802 | AC-1801..1808 | `test_plan.py`, settings UI |
| deterministic evaluation | REQ-PLAN-002 | UC-1802/1803 | AC-1805..1812 | canonical P01..P14 |
| schema v3 compatibility | REQ-PLAN-003 | UC-1804 | AC-1813..1817 | `test_settings_schema_v3.py` + legacy suites |
| configuration/inspection | REQ-PLAN-004 | UC-1801/1804 | AC-1801..1804, AC-1813..1817 | Settings UI + CLI |
| Current Details | REQ-PLAN-005 | UC-1805 | AC-1818..1821 | presenter/panel + physical |
| breach notifications | REQ-PLAN-006 | UC-1806/1807 | AC-1822..1830 | `test_plan_alerts.py` + alert harness |
| runtime integration | REQ-PLAN-007 | UC-1805/1808 | AC-1818, AC-1831..1832 | controller/redeem integration |
| protected boundaries | REQ-PLAN-008 | UC-1809 | AC-1833..1838 | architecture + full regression |

## Existing-contract coherence evidence

| Change | Historical authority | New/extended evidence |
|---|---|---|
| successful redeem + expected refetch failure preserves terminal result | v1.5 `AC-REDEEM-019` | extend `test_redeem_process_manager.py` with schema/parse error |
| duplicate normalized source window IDs fail through typed source schema error | v1.0 source fail-closed/error taxonomy | app-server parser duplicate-ID vector |
| configured LOW policy used by account presenter when v1.8 stores settings | v1.1 `AC-SETTINGS-012` | extend `test_current_account_viewmodel.py` |
| AppSettings partial edits preserve new fields | existing Settings save semantics + REQ-PLAN-003/004 | schema/UI preservation vectors |
| shared TimeToReset/FractionDelta ownership preserves old import paths | behavior-preserving refactor | existing Context/analytics suites + optional architecture invariant |

## Architectural invariants

| Invariant | Evidence |
|---|---|
| INV-PLAN-001 no History/Context authority | AST/import test |
| INV-PLAN-002 no Plan persistence subsystem | source/tree/import invariant |
| INV-PLAN-003 no Plan concurrency subsystem | AST/import test |
| INV-PLAN-004 no Plan-to-redeem mutation | import/call-boundary test + no-auto-redeem regression |
| INV-PLAN-005 one reserve owner | domain/source invariant |
| INV-PLAN-006 Budget independent | AST/import + existing Budget vectors |
| INV-PLAN-007 opaque window identity | AST/source test + dynamic-ID vectors |

## Harness reuse map

### Existing alert harness

Keep:

- baseline;
- low;
- exhausted;
- dedupe;
- rearm;
- disabled;
- restart;
- multi-window;
- failure isolation.

Add Plan variants to the same physical script.

### Existing Settings harness

Keep:

- defaults;
- value validation;
- schema 1/2 compatibility;
- no rewrite on load;
- atomic save;
- GUI Save/Cancel/Reset;
- dynamic reserve independence.

Add only schema-v3/checkpoint dimensions.

### Existing Current/redeem harness

Keep:

- one captured observation;
- refresh/adopt semantics;
- durable begin/idempotent retry;
- post-success refetch behavior;
- async UI lifecycle.

Add Plan composition/adoption evidence.

## Release-level protected evidence

The full gate must preserve all v1.0–v1.7 release families. v1.8 does not replace prior validation with new Plan-only tests.
