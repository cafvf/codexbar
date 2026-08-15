# CodexBar v1.8 — Plan Planning Record

Status: planning/specification complete; frozen for implementation
Theme: Plan
Validated release baseline: v1.7.0 — Diagnose
Initial planning baseline: `495b91c23f6d1f65e5f596280ec39730ede7c9df`
Product-spec freeze commit: `1d9f53150adb1aa6a7fb4573dab023c8bd4f4f7c`

## Planning outcome

The roadmap order remains:

- v1.8 — Plan;
- v1.9 — Explore;
- v2.0 — Activity research horizon.

Plan is intentionally before Explore because it depends primarily on capabilities already stabilized
through v1.7: authoritative Current, dynamic `UsageWindowId`, Settings, reserve/Budget semantics,
factual alerts, reset-credit safety, Current Details composition, diagnostics and release harnesses.

Historical Context is not a Plan authority or dependency.

## Frozen product model

1. Current plus explicit Settings are the only Plan authorities.
2. Existing reserve remains canonical; Plan does not own a second reserve.
3. Checkpoints are explicit per-window `(time_to_reset, minimum_remaining)` values.
4. Persisted checkpoint coordinates use whole integer seconds; the shared `TimeToReset` quantity remains generic.
5. Checkpoint selection is a step function with equality inclusive and no interpolation.
6. Effective floor is the strongest applicable reserve/checkpoint floor.
7. Plan margin is signed and distinct from Budget headroom.
8. Compliance is `ABOVE`, `AT` or `BELOW` only when an effective floor exists.
9. Checkpoint resolution is explicit and orthogonal to compliance/freshness.
10. STALE observations never advance Plan alerts and are not presented as current compliance.
11. One fixed Plan-breach notification category is opt-in and defaults off on legacy settings.
12. No forecast, probability, automatic policy adaptation or automatic redeem exists.

## Complexity outcome

Accepted new runtime semantics are deliberately small:

- pure Plan evaluation;
- in-memory Plan-breach transition tracking.

Everything else extends existing owners: AppSettings/JsonSettingsRepository, Settings UI/actions,
CurrentAccountPresenter/Current Details, TrayController adoption path and NotificationPort.

Rejected as unjustified:

- Plan repository/database/Event Store;
- Plan cache/revision;
- Plan scheduler/timer/worker;
- generic notification-rule engine/DSL;
- second settings service;
- Context/History-fed Plan logic.

## Execution model

Phase A is a coherence/specification prerequisite. Functional implementation remains four macro-parts:

1. Core Plan;
2. Settings + runtime integration;
3. UI + alerts;
4. Regression + release hardening.

`TASKS.md` decomposes these into smaller gated phases without changing that product-level structure.
Every phase preserves the existing pytest/Ruff/mypy/compileall/`git diff --check` harness and reuses
existing physical validation paths when UI/native behavior changes.
