# Phase G — Target Validation and Release Close

Goal: prove the full v1.5 system on mock/fault-injection paths and read-only real account state before
release.

## TASK-570 — Validation script

Create/update `scripts/validate_v1_5.py` with:
- automated preflight;
- reset ledger inspect;
- settings migration evidence;
- GUI Current/History regression checklist;
- reset/control checklist;
- optional real redeem check clearly marked destructive/user-explicit.

Tests:
script smoke/static validation.

## TASK-571 — Mock target validation

Validate:
- count-only;
- partial;
- complete;
- expiring;
- non-expiring;
- opportunity states;
- redeem all outcomes;
- unknown/recovery flow;
- History lifecycle.

Record evidence.

## TASK-572 — Real account read-only validation

On supported real account:
- current usage still matches;
- reset available count matches source;
- known details/expiry render when supplied;
- no extra polling side effects.

This task is PASS or capability-justified SKIP.

## TASK-573 — Optional real redeem validation

Run only on explicit user choice when a real credit can safely be spent.

Verify:
- confirmation;
- one logical attempt;
- app-server outcome;
- authoritative refetch;
- ledger evidence.

A justified SKIP does not block release if all consume behavior is covered by protocol fixtures/mock/fault
injection and the release checklist explicitly records the skip.

## TASK-574 — Full v1.4 regression target

Repeat critical v1.4 physical regressions:
- Current refresh;
- History open/hide/refresh;
- period switching;
- Ayatana/Qt fallback as applicable.

## TASK-575 — Close traceability

Replace planned test mappings with actual test identifiers.
Every P0 AC must be PASS.
P1 criteria may only be deferred by explicit release-scope decision.

## TASK-576 — Documentation close

Update:
- RELEASE.md status;
- CHANGELOG;
- README/PRODUCT_SPEC where applicable;
- validation evidence;
- FUTURE-TASKS for any non-blocking debt.

## TASK-577 — Version metadata

Bump project/package to 1.5.0 and regenerate lock metadata through normal repository tooling.

## TASK-578 — Release hygiene

Run:
- full test/lint/type/compile gates;
- `git diff --check`;
- clean status review;
- release checklist.

## TASK-579 — v1.5.0 release gate

Tag only after all mandatory Gate G evidence is PASS.
