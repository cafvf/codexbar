# CodexBar v1.8 — Test strategy and matrix

Status: implementation complete; release preparation

## 1. Harness objective

The v1.8 test plan extends the existing harness rather than replacing it.

The principal rule is:

> one new semantic dimension -> one focused vector family; do not duplicate released behavior tests.

Existing v1.0–v1.7 tests remain the regression baseline.

## 2. Implemented automated test groups

### Pure/domain/application

`tests/unit/test_plan.py`

Covers:

- checkpoint policy validation/canonicalization;
- TimeToReset observation coordinate;
- stepwise active selection;
- effective floor;
- signed margin;
- compliance;
- partial/no-policy resolution;
- canonical P01..P14 vectors.

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
- multi-window isolation;
- delivery-failure isolation;
- canonical A01..A10 semantics.

### Settings

`tests/unit/test_settings_schema_v3.py`

Covers:

- schema 3 canonical round-trip;
- v1/v2 read without rewrite;
- explicit legacy save -> v3;
- invalid v3 shape/duplicates/types.

`tests/unit/test_plan_settings_ui.py`

Covers Plan-specific UI/model behavior:

- current-window checkpoint editing;
- absent-window policy preservation;
- Save/Cancel/Reset;
- Plan notification checkbox.

Existing generic Settings tests remain authoritative for the rest.

### Current Details

`tests/unit/test_plan_panel_text.py`

Covers compact semantic render states and duration presentation without fragile full-layout snapshots.

`tests/gui/test_plan_panel.py`

Covers the Qt PlanPanel surface, ordering/content and STALE/current presentation behavior.

`tests/unit/test_plan_current_presentation.py`

Covers Plan derivation from the captured Current observation, settings application and STALE withholding.

### Runtime/alerts integration

`tests/unit/test_plan_alert_runtime_controller.py`

Covers normal refresh and authoritative `adopt_snapshot()` convergence through the same Plan alert path.

`tests/unit/test_plan_alert_validation_harness.py`

Protects the Plan scenarios added to the existing physical notification harness.

### Architecture

`tests/architecture/test_v18_plan_architecture.py`

Protects:

- no History/Context authority imports in Plan;
- no Plan persistence/concurrency subsystem;
- no Plan-to-redeem path;
- Budget does not import Plan;
- Plan does not parse `UsageWindowId`;
- shared neutral quantity ownership;
- one runtime integration seam for Plan processing.

`tests/architecture/test_v18_release_contract.py`

Protects release-prep version/document/CI coherence without asserting that the release tag already exists.

## 3. Existing tests extended, not duplicated

### `tests/unit/test_redeem_process_manager.py`

Covers terminal successful consume + expected `UsageError` refetch failure: success is retained and `refetch_error` populated.

### app-server parser tests

Cover duplicate normalized `UsageWindowId` as typed `UsageSchemaError`.

### `tests/unit/test_current_account_viewmodel.py`

Protects captured-observation reuse and released Current presentation behavior.

### `tests/unit/test_cli.py`

Extends Settings show expectations for Plan opt-in/checkpoints/schema source.

### `scripts/validate_alerts.py`

The released usage-alert scenarios remain unchanged. Plan adds focused breach/rearm/disabled/activation scenarios using the same notifier transport rather than a second physical notification script.

## 4. Canonical Plan vectors

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

Reject negative, bool and non-integer persisted values. Domain checkpoint construction also rejects sub-second coordinates so encode/decode cannot lose precision.

### S08 — invalid minimum

Reuse Fraction/Decimal-string rejection.

## 7. Architecture invariants

- `INV-PLAN-001`: Plan core imports no History/Context authority.
- `INV-PLAN-002`: no Plan persistence class/path.
- `INV-PLAN-003`: Plan core imports no concurrency/timer facilities.
- `INV-PLAN-004`: Plan alerts import no redeem/consume path.
- `INV-PLAN-005/006`: reserve owner and Budget independence.
- `INV-PLAN-007`: no duration/product parsing from `UsageWindowId` in Plan core.

All are mapped in `docs/specs/v1.8/TRACEABILITY.md`.

## 8. Mandatory existing regression families

Remain release-blocking:

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

The pre-release-prep v1.8 implementation baseline passed 815 tests. The final post-bump suite remains mandatory.

## 9. Physical target validation

Completed on target Ubuntu/GNOME/Wayland:

1. Settings opened and Plan checkpoint editor exercised;
2. add/edit/remove checkpoints;
3. Save/reopen persistence;
4. Cancel and Reset behavior;
5. PlanPanel active/configured behavior;
6. live Settings Save updates Plan without restart;
7. released usage-alert physical scenarios;
8. Plan breach/rearm/disabled/activation scenarios;
9. Current Details remained visually stable through the tested lifecycle;
10. native indicator remained usage-focused during Plan validation;
11. no duplicate-owner regression was observed in the Plan workflow;
12. no real reset credit was required.

Release-prep still requires a concise final native/window lifecycle smoke. Qt fallback remains protected by automated/released evidence; do not remove system packages merely to manufacture a physical fallback event.

Real redeem remains optional because it is destructive/consumes a real credit; mock post-redeem adoption is sufficient for v1.8 Plan integration.

## 10. Full gate

Before release-prep commit:

```bash
uv run ruff check src tests scripts --fix
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

After the version bump also run:

```bash
uv lock
uv run python scripts/validate_release_version_modes.py
```

The final exact release-prep commit must then pass hosted Python 3.12/3.13/3.14 quality jobs and the isolated uv-tool version-mode job before tag creation.

A new dependency is not justified by the v1.8 test plan.
