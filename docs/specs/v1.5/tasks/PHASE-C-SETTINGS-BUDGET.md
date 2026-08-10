# Phase C — Settings Schema v2 and Budget Core

Goal: add reserve policy using the existing canonical settings source without mixing it with reset history.

## TASK-530 — Immutable reserve policy model

Extend AppSettings application/domain model with typed per-UsageWindowId reserves.

Preserve existing low threshold/refresh/notifications behavior.

Tests:
`tests/unit/test_usage_reserve_policy.py`.

## TASK-531 — Schema-1 decode migration

Teach settings repository to read valid schema 1 into the v2 application model with empty reserves.

Reading SHALL not rewrite the file.

Tests:
`tests/unit/test_settings_schema_v1_migration.py`.

## TASK-532 — Schema-2 codec

Implement canonical schema-2 save/read with atomic replacement and strict field/value validation.

Next explicit save after schema-1 load writes schema 2.

Tests:
`tests/unit/test_settings_schema_v2.py`.

## TASK-533 — Settings origin/migration diagnostics

Represent legacy/migrated origin as needed without breaking existing callers.
Keep failure behavior for corrupt/unsupported documents explicit.

Tests:
`tests/unit/test_settings_migration_origin.py`.

## TASK-534 — Budget calculation

Implement pure:
- NO_POLICY;
- ABOVE_RESERVE;
- AT_RESERVE;
- BELOW_RESERVE;
- exact `max(R-reserve,0)` headroom.

Define comparison using exact Fraction/Decimal semantics rather than display rounding.

Tests:
`tests/unit/test_budget_policy.py`.

## TASK-535 — Runtime reserve application

Expose reserve changes to current/control application state without restart.
Do not modify UsageWindowState/UsagePolicy.

Tests:
`tests/unit/test_budget_runtime.py`.

## TASK-536 — Settings CLI regression

`settings show/reset` remains correct with schema 2 and can present reserve policies deterministically.

Tests:
existing settings acceptance + `tests/acceptance/test_settings_v2_cli.py`.

## TASK-537 — Migration architecture/regression tests

Protect:
- one settings source;
- no control-policy sidecar file;
- schema-1 backward compatibility;
- schema-2 canonical write.

Tests:
`tests/architecture/test_v1_5_settings_architecture.py`.

## TASK-538 — Reserve test fixtures for Current windows

Add deterministic fixtures for weekly/5h/new unknown window IDs used by monitor/UI phases.
No production UI yet.

## TASK-539 — Phase C regression gate

Run Gate C.
