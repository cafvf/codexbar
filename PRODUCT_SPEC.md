# CodexBar Product Specification

Status: v1.4.0 validated release
Current validated release: 1.4.0
Theme: Understand

## Purpose
Provide a small Linux desktop monitor for current Codex usage plus bounded, deterministic insight over observations retained locally by CodexBar.

## Product truth
CodexBar reports what a verified Codex source exposes. Historical data are discrete observations, not continuous measurement or authoritative token accounting.

## Stable domain vocabulary
- **Usage window:** independently reported quota/rate-limit window.
- **UsageWindowId:** opaque stable identity supplied by the adapter/presentation contract.
- **Remaining fraction:** normalized Decimal value in `[0,1]`.
- **Snapshot:** immutable current observation.
- **Freshness:** CURRENT or STALE source state.
- **Historical snapshot/sample:** persisted eligible CURRENT observation and per-window time context.
- **Analysis period:** read-only 24h/7d/30d half-open interval `[start,end)`.
- **Observed change/increase:** factual relationship between retained samples, not inferred consumption/reset.

## Validated release evolution
### v1.0 — Observe
Verified provider, normalized windows, CURRENT/STALE fallback, Linux tray and user-local desktop integration.
### v1.1 — Configure
Schema-v1 settings, LOW policy, refresh cadence and notification enablement.
### v1.2 — Notify
Transition-based LOW/EXHAUSTED alerts with stale/error isolation.
### v1.3 — Remember
Schema-v1 SQLite CURRENT-only observation history, fixed 30-day retention, inspect/clear and failure isolation.
### v1.4 — Understand
1. Read-only descriptive analytics over retained observations.
2. Observation count, first/latest, observed min/max/change and observed increases without forecast/interpolation.
3. History UI with 24h/7d/30d and an explicit time domain ending at the captured request end instant.
4. Period-only History UX; stable focused `UsageWindowId` remains internal and never silently falls back to another identity.
5. Richer CURRENT cards with whole-percent compatibility, classification, freshness/age and reset presentation.
6. CURRENT -> History navigation by stable identity.
7. GUI lifecycle stabilization: single composition, render-on-state-transition and independent Current/History ownership.
8. No history/settings schema migration.

## Non-functional invariants
- domain/application behavior remains headless and deterministic;
- UI does not import concrete infrastructure;
- analytics does not depend directly on Qt or SQLite;
- history is read-only for analytical/UI interactions and never becomes CURRENT fallback;
- STALE snapshots are not persisted as new historical observations;
- current refresh remains asynchronous/non-overlapping;
- unexpected secondary-capability failures do not fabricate source failure;
- native system-Python helper remains isolated and Qt fallback remains part of the product contract;
- persistence-format evolution requires an explicit compatibility decision.

## Explicitly deferred beyond v1.4
- forecasting or time-to-exhaustion;
- authoritative token-consumption estimation;
- interpolation or continuous trajectory reconstruction;
- arbitrary historical-only window browsing in the History UI;
- configurable retention/cloud/remote/account analytics;
- persistence schema v2;
- native packaging beyond the validated uv/XDG workflow.

Maintenance warnings/deprecations are tracked in `docs/FUTURE-TASKS.md`.
