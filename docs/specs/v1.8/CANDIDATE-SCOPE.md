# CodexBar v1.8 — Scope Resolution

Status: frozen for implementation
Theme: Plan

Normative semantics are owned by `PRODUCT.md`, `DECISIONS.md` and `REQUIREMENTS.md`.

## Included

- explicit checkpoint policy by opaque dynamic `UsageWindowId`;
- checkpoint coordinate expressed as whole-second persisted time-to-reset duration;
- minimum-remaining floor per checkpoint;
- step-function active-checkpoint selection without interpolation;
- reuse of the existing canonical `UsageReservePolicy`;
- effective floor as the maximum applicable reserve/checkpoint floor;
- signed Plan margin using the shared `FractionDelta` quantity;
- deterministic `ABOVE` / `AT` / `BELOW` compliance when an effective floor exists;
- explicit checkpoint resolution for not-configured, missing/invalid reset, no-active-checkpoint and active cases;
- partial capability when factual reset time is unavailable;
- non-monotonic checkpoint policies permitted;
- unique checkpoint coordinates per window;
- Settings schema v3 with schema-v1/v2 read compatibility and explicit-save upgrade;
- typed checkpoint editing in the existing Settings experience;
- Plan presentation composed into Current Details;
- STALE-aware presentation with no stale-triggered Plan side effects;
- one opt-in factual Plan-breach notification category;
- preservation of existing Current, Budget/Control, History/Context and manual redeem authority.

## Evidence-gated / explicitly not core

Reset-credit expiry/count-change notifications are not required by v1.8 Plan. They remain outside
core scope unless a later specification amendment establishes a factual supported runtime contract.

## Deferred to v1.9 Explore or later

- explainable Historical Context evidence selection;
- Cycle Explorer;
- richer History views/export;
- support bundle/export features;
- Activity/session inference;
- account-aware analytics/schema evolution.

## Prohibited in v1.8

- forecasting future consumption;
- time-to-exhaustion estimates;
- probability of exhaustion;
- interpolation between checkpoints;
- History/Context influence on Plan evaluation or alerts;
- generic notification-rule DSL/engine;
- automatic policy adaptation;
- automatic reset-credit redemption;
- Plan database/Event Store/cache/scheduler/worker introduced without a new justified decision.

## Complexity rule

A new abstraction or state owner is permitted only when it removes demonstrated duplication or is
required by a frozen REQ/AC. Test-harness growth must remain proportional to new semantics, preferring
parameterized vectors and existing integration seams over parallel frameworks.
