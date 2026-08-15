# ADR-008 — Settings schema v3 for explicit Plan policy

Status: accepted
Date: 2026-08-14
Release: v1.8

## Context

ADR-005 established CodexBar Settings persistence as an explicit versioned compatibility boundary and requires a deliberate decision for future schema versions.

v1.5 released schema 2 by adding per-window `usage_reserves`.

v1.8 Plan requires persistent user intent for:

- per-window checkpoint targets;
- whether factual Plan breach notifications are enabled.

These values belong to AppSettings rather than a new Plan database because they are configuration, not observational/runtime state.

## Decision

1. Canonical Settings schema becomes version 3.
2. Existing schema-2 fields and meanings remain unchanged.
3. `usage_reserves` remains the sole persisted reserve policy.
4. Add:
   - `usage_plan_checkpoints`;
   - `plan_breach_notifications_enabled`.
5. Schemas 1 and 2 remain readable.
6. Legacy reads create in-memory Plan defaults:
   - empty checkpoint policy;
   - Plan breach notifications disabled.
7. Merely reading schema 1/2 does not rewrite the file.
8. The next explicit valid Save writes canonical schema 3.
9. Schema 3 retains exact-key validation.
10. Fractions remain Decimal strings.
11. Persisted Plan checkpoint coordinates are constrained to whole seconds and serialized as non-negative integer `time_to_reset_seconds`.
12. Window IDs are JSON object keys and remain opaque; persistence does not parse product duration from them.
13. Checkpoints are canonically ordered descending by time-to-reset for each lexicographically ordered window ID.
14. Writes retain existing sibling-temp-file, flush/fsync and atomic-replace behavior.
15. Unsupported future schemas continue to fail closed for that persisted document and fall back according to existing Settings behavior.
16. Downgrade-read compatibility is not promised: a pre-v1.8 binary may reject a schema-3 document.

## Canonical shape

```json
{
  "schema_version": 3,
  "low_remaining_threshold": "0.20",
  "refresh_interval_seconds": 60,
  "notifications_enabled": true,
  "usage_reserves": {
    "window_10080m": "0.15"
  },
  "usage_plan_checkpoints": {
    "window_10080m": [
      {
        "time_to_reset_seconds": 259200,
        "minimum_remaining": "0.55"
      },
      {
        "time_to_reset_seconds": 86400,
        "minimum_remaining": "0.30"
      }
    ]
  },
  "plan_breach_notifications_enabled": false
}
```

## Why flat fields

A nested `plan_policy` object was rejected because reserve already has a released canonical location.

Moving/duplicating reserve would create a migration and two plausible owners for the same user intent.

Flat additive fields minimize compatibility cost.

## Why integer seconds

Plan checkpoint policy is constrained to whole-second coordinates. This keeps schema-v3 encode/decode
exact without narrowing the shared `TimeToReset` quantity used elsewhere.

Rejected alternatives:

### Duration strings such as `72h`

They require a new parser/grammar, canonicalization rules and additional malformed-input cases.

### Floating-point hours

They introduce binary floating-point ambiguity into an otherwise Decimal/typed settings boundary.

### Upstream-style duration minutes as semantic identity

Checkpoint coordinate is independent of the adapter's current `windowDurationMins`. Persisting seconds keeps the unit generic and lossless.

## Why no Plan database

Checkpoints are user configuration, not observations or events.

A second persistence subsystem would create unnecessary lifecycle, failure and diagnostic states.

## Notification compatibility

`plan_breach_notifications_enabled` defaults to false for:

- application defaults;
- schema-1 loads;
- schema-2 loads.

This prevents an upgrade from creating a new notification category for users who previously enabled general usage notifications.

The existing global `notifications_enabled` remains the master delivery gate.

## Consequences

Positive:

- no second configuration store;
- reserve semantics unchanged;
- deterministic legacy defaults;
- no duration parser;
- existing atomic persistence/harness reused.

Costs:

- one schema version increment;
- explicit v1/v2/v3 compatibility tests;
- older CodexBar versions cannot interpret schema 3 after an explicit v1.8 save.

## Validation

Required implementation/validation evidence:

- schema 3 canonical round-trip;
- schema 1/2 read without rewrite;
- explicit legacy Save -> schema 3;
- exact-key/type/duplicate validation;
- atomic-write regression;
- GUI Save/Cancel/Reset;
- CLI inspection.
