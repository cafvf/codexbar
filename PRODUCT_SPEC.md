# CodexBar Product Specification

Status: v1.8 specification frozen for implementation
Current validated release: v1.7.0 — Diagnose
Active specification: v1.8 — Plan
Theme: Plan

## Purpose

Provide a small Linux desktop monitor for current Codex usage plus bounded, deterministic insight over locally retained observations and explicit, recoverable reset-credit control.

## Product truth

CodexBar reports what a verified Codex source exposes. Historical data are discrete observations, not continuous measurement or authoritative token accounting. Reset-credit state is authoritative only when supplied by the current account read; the reset ledger records evidence but never replaces current state.

## Stable domain vocabulary

- **Usage window:** independently reported quota/rate-limit window.
- **UsageWindowId:** opaque stable identity supplied by the adapter/presentation contract.
- **Remaining fraction:** normalized Decimal value in `[0,1]`.
- **Snapshot:** immutable current usage observation.
- **Freshness:** CURRENT or STALE source state.
- **Historical snapshot/sample:** persisted eligible CURRENT usage observation.
- **Reset-credit inventory:** current authoritative count plus optional per-credit detail.
- **Reset event ledger:** append-only evidence of observed reset-credit changes and redeem attempts/outcomes.
- **Usage reserve:** user policy keyed by `UsageWindowId`.
- **Usable headroom:** `max(remaining - reserve, 0)`.
- **Redeem attempt:** durable destructive operation identified by an idempotency key.
- **OUTCOME_UNKNOWN:** consume may have reached the source but the client cannot safely infer the result.

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
Read-only descriptive analytics, History UI, richer CURRENT details and stabilized GUI lifecycle.

### v1.5 — Control
1. One composed account read produces current usage plus reset-credit capability.
2. `UsageSnapshot` remains free of reset-credit state.
3. Reset-credit evidence is persisted in an independent append-only event ledger.
4. Settings schema v2 adds per-window usage reserves while schema v1 remains readable without rewrite-on-load.
5. Budget/headroom and reset-opportunity policy are deterministic and do not forecast consumption.
6. Redeem is manual, explicit, confirmation-gated, durable and idempotent.
7. Ambiguous transport outcomes remain `OUTCOME_UNKNOWN`; recovery reuses the original attempt id.
8. Reset-credit expiry monitoring is factual and distinct from advisory policy.
9. Current Details composes usage, reset capability, budget/control and redeem recovery without modifying RichUsagePanel semantics.
10. Native indicator/tray glance remains usage-focused; reset detail stays in Current Details.
11. Mock/fault-injection validation covers destructive behavior without spending real credits.
12. Real redeem validation is optional because it consumes a real credit.

### v1.6 — Context
1. Usage History retention expands to 180 days while remaining schema v1 and CURRENT-only.
2. Context is anchored on authoritative `resets_at - observed_at` time-to-reset.
3. Historical cycle identity is `(UsageWindowId, resets_at)`.
4. Each prior cycle contributes at most one nearest real retained observation; no interpolation is introduced.
5. Comparable-cycle tolerance is exactly `min(0.05*h*, 2 hours)`, inclusive.
6. Coverage is based on independent comparable cycles: 0–2 Insufficient, 3–4 Sparse, 5–9 Limited, 10+ Established.
7. Empirical median/range/quartiles/rank adapt to coverage and preserve ties explicitly.
8. Historical context is a separate Open Details surface and does not enter the tray/native glance.
9. Context failure is isolated from Current usage.
10. Context has no authority over alerts, Control/Budget, notifications, or reset-credit redeem.
11. Schema v1 and current indexes are retained after 180-day performance characterization.
12. Real-account validation is read-only; missing runtime capability may be recorded as an explicit release SKIP.

### v1.7 — Diagnose
1. Doctor text, JSON diagnostics and System Health share one typed diagnostic model.
2. Doctor/System Health remain read-only and minimize secret/account-identifying output.
3. Runtime diagnostic metrics are local, in-memory, bounded and use monotonic duration measurement.
4. One normal GUI process owns polling, notifications, desktop indicator and redeem interaction per user/session.
5. A second GUI launch requests `SHOW_DETAILS` from the existing owner and exits.
6. Historical Context uses Current/History revisions, a lean schema-v1 candidate projection and revision-aware caching without changing v1.6 semantics.
7. Context repository/summary computation and external redeem/refetch work execute outside the Qt interaction thread.
8. Stale async Context results and obsolete/closed redeem completions cannot overwrite newer state or resurrect closed UI.
9. System Health is a separate auto-updating read-only window; Open Details owns authoritative manual Refresh.
10. Account lineage is explicit: v1.7 local History assumes one ChatGPT account and is not durably namespaced by a supported stable account identifier.
11. Budget without a configured reserve reports headroom as not applicable.
12. The native Ayatana helper remains supported with bounded stderr diagnostics, dynamic label guidance and Qt fallback.
13. `pyproject.toml` is the single release-version authority and hosted CI covers Python 3.12, 3.13 and 3.14.
14. Evidence-gated app-server, prune, WAL and Ayatana changes were evaluated and intentionally retained without speculative migration.

## Active specification — v1.8 Plan

v1.8 is frozen for implementation but is not yet a validated release.

Its product question is:

> How does Current compare with the plan I explicitly configured for this window?

The frozen scope adds explicit per-window time-to-reset checkpoints, composes them with the existing
usage reserve, shows a deterministic signed margin/compliance result in Current Details, and optionally
notifies on a factual transition into below-plan state.

Plan uses only Current plus explicit Settings and the observation timestamp. History, Historical Context,
consumption-rate inference, forecasting, probability and automatic reset-credit redemption have no Plan
authority.

## Non-functional invariants

- domain/application behavior remains headless and deterministic except explicit composition boundaries;
- `UsageProvider` remains compatible with legacy CLI/tests;
- history SQLite remains schema 1 and CURRENT-only;
- reset ledger is independent from history/settings persistence;
- UI does not read concrete repositories directly;
- no automatic redeem exists;
- monitoring does not depend on forecast, slope or history;
- current account operations share one serialized lane;
- native system-Python helper remains isolated and Qt fallback remains part of the product contract;
- persistence-format evolution requires an explicit compatibility decision.

## Explicitly deferred from v1.8 Plan

- forecasting or time-to-exhaustion;
- authoritative token-consumption estimation;
- automatic reset-credit redemption;
- cloud/remote/account analytics;
- native packaging beyond the validated uv/XDG workflow.

Maintenance warnings/deprecations remain tracked in `docs/FUTURE-TASKS.md`.
