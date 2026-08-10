# REQ-BUDGET-001 — Usage reserve in AppSettings schema v2

Status: reviewed draft
Priority: P1
Release: v1.5
Change taxonomy: CONTROL POLICY / SETTINGS MIGRATION

## Requirement

CodexBar SHALL allow the user to define an explicit remaining-quota reserve by stable `UsageWindowId`.

Reserve SHALL be part of the canonical application settings model and persistence schema v2.

A separate control-policy configuration file SHALL NOT be introduced in v1.5.

## Core calculation

For current remaining fraction `R` and configured reserve `R_reserve`:

`headroom = max(R - R_reserve, 0)`

Budget status is independent from normal usage classification:

- `NO_POLICY`
- `ABOVE_RESERVE`
- `AT_RESERVE`
- `BELOW_RESERVE`

Reserve SHALL NOT change LOW/EXHAUSTED classification.

## Settings model

`AppSettings` schema v2 adds per-window reserves keyed by stable `UsageWindowId`.

Application representation SHOULD remain immutable, for example a tuple of typed reserve entries rather
than exposing a mutable dictionary inside a frozen settings object.

JSON representation MAY use a map keyed by `UsageWindowId.value`.

Example:

```json
{
  "schema_version": 2,
  "low_remaining_threshold": "0.20",
  "refresh_interval_seconds": 60,
  "notifications_enabled": true,
  "usage_reserves": {
    "window_10080m": "0.15"
  }
}
```

## Schema migration

Valid schema-1 settings SHALL be accepted.

On schema-1 read:
- parse existing values exactly under their v1 contract;
- create the schema-v2 in-memory `AppSettings` with no reserve policies;
- report a migrated/legacy origin if useful;
- DO NOT rewrite the settings file merely because it was read.

On the next explicit settings save:
- write canonical schema 2 atomically.

Unsupported/corrupt schemas continue to fail closed under existing settings behavior.

## Stable identity

Reserve key is `UsageWindowId`.

No policy may be inherited by:
- human label;
- window position;
- guessed duration alias.

Unknown/new stable IDs default to `NO_POLICY`.

## Use cases

### UC-BUDGET-001 — Existing v1 user

User upgrades with schema-1 settings.

CodexBar loads all prior settings unchanged and has no reserve policies until configured.

### UC-BUDGET-002 — Configure weekly reserve

Weekly remaining 43%, reserve 15% -> headroom 28pp.

### UC-BUDGET-003 — Below reserve

Remaining 10%, reserve 15% -> headroom 0 and budget status BELOW_RESERVE.
Usage state remains governed by existing UsagePolicy.

### UC-BUDGET-004 — Runtime change

Reserve changes while app is running and control assessment updates without restart.

## Acceptance criteria

- `AC-BUDGET-001`: reserve uses existing Fraction semantics and validates [0,1].
- `AC-BUDGET-002`: reserve is keyed only by UsageWindowId.
- `AC-BUDGET-003`: headroom equals max(R-reserve,0).
- `AC-BUDGET-004`: no policy differs from explicit zero reserve.
- `AC-BUDGET-005`: reserve does not alter UsageWindowState.
- `AC-BUDGET-006`: unknown window IDs do not inherit another policy.
- `AC-BUDGET-007`: valid schema 1 loads into schema-v2 application model with empty reserves.
- `AC-BUDGET-008`: reading schema 1 causes no automatic file rewrite.
- `AC-BUDGET-009`: next explicit save writes schema 2.
- `AC-BUDGET-010`: schema-v2 persistence remains atomic.
- `AC-BUDGET-011`: corrupt/unsupported settings fail according to established settings safety semantics.
- `AC-BUDGET-012`: reserve changes apply at runtime.
- `AC-BUDGET-013`: ResetOpportunityPolicy may read reserve/headroom but cannot mutate settings.
- `AC-BUDGET-014`: budget uses current usage only; history/ledger are not current fallback.
- `AC-BUDGET-015`: budget performs no future-consumption extrapolation.
- `AC-BUDGET-016`: UI distinguishes quota remaining, reserve and usable headroom.
- `AC-BUDGET-017`: existing low threshold, refresh interval and notification enablement remain behaviorally
  unchanged during v1->v2 migration.

## Deferred

Time-varying budget envelopes and probabilistic historical control context belong to later releases.

## Implementation mapping

Primary task range: `TASK-530..539`.
Detailed AC-to-task/test mapping: `TRACEABILITY.md`.
