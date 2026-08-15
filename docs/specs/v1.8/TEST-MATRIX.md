# CodexBar v1.8 — Test strategy and matrix

Status: frozen for implementation

## 1. Harness objective

The v1.8 test plan MUST extend the existing harness rather than replace it.

The principal rule is:

> one new semantic dimension -> one focused vector family; do not duplicate released behavior tests.

Existing v1.0–v1.7 tests remain the regression baseline.

## 2. Planned new automated test groups

Keep the new-file count small.

### Pure/domain/application

`tests/unit/test_plan.py`

Covers:

- checkpoint policy validation/canonicalization;
- TimeToReset observation coordinate;
- stepwise active selection;
- effective floor;
- signed margin;
- compliance;
- partial/no-policy resolution.

Use parameterized canonical vectors instead of one test per branch.

`tests/unit/test_plan_alerts.py`

Covers transition state machine:

- baseline;
- breach;
- dedupe;
- rearm;
- disabled delivery/no replay;
- stale;
- checkpoint activation;
- policy rebaseline;
- cycle rebaseline;
- reset missing/invalid eligibility;
- multi-window isolation.

### Settings

`tests/unit/test_settings_schema_v3.py`

Covers:

- schema 3 canonical round-trip;
- v1/v2 read without rewrite (parameterized);
- explicit legacy save -> v3;
- invalid v3 shape/duplicates/types.

Do not copy all existing schema-v1/v2 tests.

`tests/unit/test_plan_settings_ui.py`

Covers only Plan-specific UI/model behavior:

- current-window checkpoint edit;
- absent-window policy preservation;
- Save/Cancel/Reset;
- Plan notification checkbox.

Existing generic Settings tests remain authoritative for the rest.

### Current Details

`tests/unit/test_plan_panel.py`

Covers compact render states:

- not configured;
- active/checkpoint-dominant;
- reserve-dominant;
- no active checkpoint;
- reset unavailable;
- stale.

Use semantic text assertions, not fragile full-layout snapshots.

### Architecture

`tests/architecture/test_v18_plan_architecture.py`

Protect:

- no History/Context authority imports in Plan;
- no Plan persistence/concurrency subsystem;
- no Plan-to-redeem path;
- Budget does not import Plan;
- Plan does not parse `UsageWindowId`;
- shared neutral quantity ownership where appropriate.

Use AST/import checks consistent with existing architecture harness style.

### Integration/acceptance

`tests/acceptance/test_v18_plan_runtime.py` or the existing equivalent acceptance location.

Covers:

- normal refresh -> Plan evaluation/alerts;
- post-redeem `adopt_snapshot()` -> same Plan alert path;
- live settings update affects next evaluation without restart;
- no extra source read.

If existing test files already provide the same harness seam, extend them rather than add this file.

## 3. Existing tests to extend, not duplicate

### `tests/unit/test_redeem_process_manager.py`

Add one vector:

- terminal successful consume + `UsageSchemaError` refetch -> success retained and `refetch_error` populated.

This closes existing `AC-REDEEM-019`.

### app-server parser tests

Add one source vector:

- primary/secondary normalize to duplicate `UsageWindowId` -> typed `UsageSchemaError`.

### `tests/unit/test_current_account_viewmodel.py`

Add:

- non-default LOW threshold is honored by presenter once it stores AppSettings;
- Plan is derived from the captured observation without second read.

### `tests/unit/test_cli.py`

Extend Settings show expectations for:

- Plan opt-in;
- checkpoint rendering;
- schema source.

### `scripts/validate_alerts.py` + `test_alert_validation_harness.py`

Keep all existing usage-alert scenarios unchanged.

Add a small Plan scenario namespace, for example:

```text
plan-baseline
plan-breach
plan-dedupe
plan-rearm
plan-disabled
plan-checkpoint
plan-cycle
plan-policy
```

The physical harness should use the same notifier transport.

Avoid creating a second near-duplicate physical notification script.

## 4. Canonical Plan vectors

Use one table-driven pure evaluator suite.

| Vector | Reserve | Checkpoints | ttr/reset | Remaining | Expected |
|---|---:|---|---|---:|---|
| P01 | none | none | any | 63% | not configured; no floor/compliance |
| P02 | 15% | none | reset absent | 63% | floor 15%; margin +48pp; ABOVE |
| P03 | none | 72h→55% | 100h | 63% | no active checkpoint; no floor |
| P04 | none | 72h→55% | exactly 72h | 55% | active; AT |
| P05 | none | 72h→55%,24h→30% | 60h | 50% | 55% active; -5pp; BELOW |
| P06 | 60% | 72h→55% | 60h | 63% | floor 60% reserve; +3pp |
| P07 | 15% | 72h→55% | 60h | 63% | floor 55% checkpoint; +8pp |
| P08 | 55% | 72h→55% | 60h | 55% | tie; AT |
| P09 | 15% | 72h→55% | reset missing | 12% | RESET_MISSING; reserve floor; BELOW display assessment |
| P10 | none | 72h→55% | reset missing | 63% | RESET_MISSING; no compliance |
| P11 | 15% | 72h→55% | reset before observed | 20% | RESET_INVALID; reserve-only display assessment |
| P12 | none | 72h→40%,24h→60% | 20h | 55% | non-monotonic accepted; 60% active; BELOW |
| P13 | 15% | 72h→55% | 80h | 10% | no active checkpoint; reserve floor; BELOW |
| P14 | none | 0h→10% | exactly reset instant | 10% | zero-duration checkpoint active; AT |

## 5. Canonical Plan-alert sequences

### A01 — baseline already below

```text
CURRENT BELOW -> baseline, no notification
```

### A02 — breach and dedupe

```text
ABOVE -> BELOW -> BELOW
        one event
```

### A03 — rearm

```text
ABOVE -> BELOW -> ABOVE -> BELOW
        event             event
```

### A04 — delivery disabled

```text
ABOVE(disabled)
-> BELOW(disabled)
-> BELOW(enabled)
```

No delivery/replay. Tracker has already advanced.

### A05 — checkpoint activation

Same policy/cycle:

```text
NO ACTIVE (compliance None)
-> checkpoint ACTIVE and BELOW
```

One event.

### A06 — policy edit

```text
ABOVE under policy A
-> BELOW under policy B
```

Policy B observation becomes silent baseline.

### A07 — new cycle

```text
BELOW cycle A
-> BELOW cycle B (new resets_at)
```

Cycle B observation becomes silent baseline.

### A08 — reset capability missing

Checkpoints configured:

```text
valid baseline
-> RESET_MISSING and reserve BELOW
-> valid same/new cycle
```

No event while missing. Return follows cycle/baseline rules.

### A09 — stale

```text
ABOVE current
-> BELOW stale
-> BELOW current
```

STALE neither emits nor advances; the final CURRENT transition may emit.

### A10 — multi-window

Two independent window policies cross in one snapshot; two distinct Plan events are produced/delivered.

## 6. Settings vectors

### S01 — defaults

```text
usage_plan_checkpoints = empty
plan_breach_notifications_enabled = false
```

### S02 — v1 load

No rewrite; effective new Plan defaults.

### S03 — v2 load with reserve

Reserve preserved; Plan defaults; no rewrite.

### S04 — explicit save from v1/v2

Writes canonical schema 3.

### S05 — round-trip

Multiple windows + multiple checkpoints + reserve + Plan opt-in.

### S06 — duplicate checkpoint time

Typed document/validation failure.

### S07 — invalid seconds

Reject negative, bool and non-integer persisted values. Domain checkpoint construction also rejects
sub-second coordinates so encode/decode cannot lose precision.

### S08 — invalid minimum

Reuse Fraction/Decimal-string rejection.

## 7. Architecture invariants

Prefer a handful of robust AST/import assertions over dozens of source-string tests.

Minimum:

- `INV-PLAN-001`: Plan core imports no History/Context authority.
- `INV-PLAN-002`: no Plan persistence class/path.
- `INV-PLAN-003`: Plan core imports no concurrency/timer facilities.
- `INV-PLAN-004`: Plan alerts import no redeem/consume path.
- `INV-PLAN-005/006`: reserve owner and Budget independence.
- `INV-PLAN-007`: no duration parsing from `UsageWindowId` in Plan core.

## 8. Mandatory existing regression families

Remain green:

- app-server source fixtures;
- refresh/current STALE and fail-closed behavior;
- configurable LOW policy;
- usage alert transition harness;
- settings v1/v2 compatibility;
- History capture/query/retention;
- History analytics;
- v1.6 Context canonical vectors;
- v1.7 Context revisions/cache/async stale-result rejection;
- Budget reserve/headroom;
- reset opportunity/monitor;
- reset ledger;
- redeem durability/idempotency/unknown outcome;
- Current Details/History/Context/System Health lifecycle;
- single-instance ownership;
- native Ayatana + Qt fallback;
- CLI;
- hosted Python 3.12/3.13/3.14 CI contract.

## 9. Physical target validation

Required on target Ubuntu/GNOME/Wayland:

1. open Settings from native/fallback menu;
2. add/edit/remove Plan checkpoints for current windows;
3. Save and reopen; values persist;
4. Cancel leaves values unchanged;
5. PlanPanel renders configured/no-active/active states using mock/current data;
6. live Settings Save updates Plan without restart;
7. run existing usage-alert physical scenarios;
8. run Plan breach/rearm/disabled physical scenarios;
9. Open Details close/reopen remains stable;
10. native indicator remains usage-focused;
11. no duplicate GUI owner;
12. no real reset credit is required.

Real redeem remains optional because it is destructive/consumes a real credit; mock post-redeem adoption is sufficient for v1.8 Plan integration.

## 10. Full gate

Before phase completion:

```bash
uv run ruff check src tests scripts --fix
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

A new dependency is not justified by the v1.8 test plan.
