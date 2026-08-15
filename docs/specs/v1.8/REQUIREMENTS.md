# CodexBar v1.8 — Requirements

Status: frozen for implementation
Theme: Plan

## Requirement conventions

- MUST: release-blocking.
- SHOULD: expected behavior with documented exception allowed.
- MAY: optional.
- Architectural implementation constraints that do not create user behavior are `INV-PLAN-*`, not separate product REQs.

## REQ-PLAN-001 — Explicit per-window checkpoint policy

CodexBar MUST allow explicit Plan checkpoints keyed by opaque `UsageWindowId`.

Each checkpoint MUST contain:

- a non-negative `TimeToReset`;
- `minimum_remaining: Fraction`.

A persisted Plan checkpoint MUST use a whole-second `TimeToReset` coordinate so schema-v3 integer
seconds round-trip without precision loss.

For one window, duplicate `TimeToReset` coordinates MUST be rejected.

Checkpoint floors MAY be non-monotonic.

The existing `UsageReservePolicy` MUST remain the only reserve configuration authority.

## REQ-PLAN-002 — Deterministic factual Plan evaluation

For each observed window, CodexBar MUST be able to evaluate explicit Plan policy without forecasting.

Checkpoint coordinate MUST derive from:

```text
resets_at - observed_at
```

not render-time wall clock.

Checkpoint selection MUST be stepwise with inclusive thresholds and no interpolation.

The effective floor MUST be the maximum of the configured reserve and active checkpoint minimum among factually available components.

The result MUST distinguish:

- checkpoint resolution;
- effective floor when one exists;
- signed `FractionDelta` margin when one exists;
- `ABOVE`, `AT`, or `BELOW` compliance when an effective floor exists.

Missing/invalid reset MUST NOT fabricate checkpoint state.

## REQ-PLAN-003 — Settings schema v3 and compatibility

AppSettings persistence MUST evolve to schema 3 while preserving the existing persistence boundary.

Schema 3 MUST add:

- `usage_plan_checkpoints`;
- `plan_breach_notifications_enabled`.

Schemas 1 and 2 MUST remain readable.

Reading legacy schema MUST NOT rewrite the managed file.

The next explicit Save MUST write canonical schema 3.

Schema-v3 writes MUST retain existing atomic-write, exact-key and Decimal-string behavior.

Partial settings updates MUST preserve unedited settings and policies.

## REQ-PLAN-004 — Plan configuration and inspection

The GUI Settings surface MUST allow the user to inspect and edit checkpoint policy for currently reported dynamic windows without parsing current usage values into policy.

The editor MUST support add/remove/update behavior with typed validation rather than an undocumented free-text policy language.

Policies belonging to currently absent windows MUST be preserved.

`codexbar settings show` MUST expose effective Plan checkpoint configuration, Plan breach notification opt-in, origin and source schema metadata.

Save/Cancel/Reset behavior MUST remain consistent with existing Settings semantics.

## REQ-PLAN-005 — Current Details Plan presentation

Current Details MUST expose a Plan section derived from the same captured Current observation used by existing Current-derived surfaces.

For CURRENT data it MUST distinguish at least:

- not configured;
- configured but no checkpoint active;
- checkpoint reset unavailable/invalid;
- active checkpoint;
- effective floor;
- signed margin;
- compliance.

The Plan section SHOULD identify whether reserve, checkpoint, or both determine the effective floor.

STALE data MUST NOT be presented as current Plan compliance.

Budget headroom/reset recommendation semantics MUST remain owned by Control/Budget.

## REQ-PLAN-006 — Factual Plan breach notifications

CodexBar MUST support one optional factual Plan breach notification category.

Delivery requires both:

```text
notifications_enabled
plan_breach_notifications_enabled
```

Plan breach opt-in MUST default to false for defaults and legacy-schema loads.

Evaluation MUST be CURRENT-only.

The first eligible observation for a window/policy/cycle MUST be a silent baseline.

A transition into `BELOW` MUST emit at most one event until compliance recovers to `ABOVE` or `AT`.

Delivery-disabled transitions MUST still update tracker state so re-enabling notifications does not replay an old breach.

Relevant Plan policy changes and new resolved reset cycles MUST establish a new silent baseline.

Configured checkpoints with missing/invalid reset MUST NOT generate Plan breach events.

No Plan notification may trigger automatic redeem or another account mutation.

## REQ-PLAN-007 — Existing runtime-path integration

Plan evaluation and Plan alerting MUST use existing authoritative snapshot paths.

Normal refresh and authoritative post-redeem `adopt_snapshot()` MUST converge through the same Plan alert/evaluation semantics.

Live Settings Save MUST apply Plan policy without process restart.

Plan evaluation MUST remain synchronous/pure and MUST NOT introduce a Plan-specific worker, executor, repository, cache, revision, scheduler or persistent event state.

## REQ-PLAN-008 — Protected authority and regression boundaries

v1.8 MUST preserve:

- Current as sole current-usage authority;
- dynamic opaque `UsageWindowId`;
- existing LOW/EXHAUSTED usage-alert semantics;
- Budget reserve/headroom semantics;
- reset-opportunity policy semantics;
- History observational authority only;
- Context descriptive authority only;
- manual/durable/idempotent redeem;
- single-instance GUI ownership;
- native Ayatana/Qt fallback behavior;
- History and reset-ledger persistence boundaries.

Plan calculation MUST NOT consume History, Historical Context, reset ledger, reset-credit inventory, inferred consumption rate or predicted future state.

No forecasting, time-to-exhaustion estimate, exhaustion probability or automatic redeem is introduced.

## Architectural invariants

### INV-PLAN-001 — No Context/History authority dependency

Core Plan evaluation modules MUST NOT import or call History/Context services/repositories.

Neutral shared quantities MAY be used by both features.

### INV-PLAN-002 — No Plan persistence subsystem

No Plan-specific SQLite repository, Event Store, cache or durable tracker exists.

Checkpoint persistence is owned by AppSettings.

### INV-PLAN-003 — No Plan concurrency subsystem

Core Plan evaluation does not import/use executors, threads, async workers or timers.

### INV-PLAN-004 — No Plan-to-redeem mutation path

Plan/Plan alerts cannot call reset consume, redeem process manager or other destructive account ports.

### INV-PLAN-005 — Reserve has one owner

`UsageReservePolicy` remains the only configured reserve source; checkpoint models contain no duplicate reserve field.

### INV-PLAN-006 — Budget remains Plan-independent

Existing Budget calculation does not import checkpoint/Plan evaluation and its released outputs remain unchanged for identical reserve/current inputs.

### INV-PLAN-007 — Window identity remains opaque

Plan domain/application/settings code does not parse duration/product semantics from `UsageWindowId`.
