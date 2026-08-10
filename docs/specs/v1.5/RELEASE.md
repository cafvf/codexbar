# CodexBar v1.5 Release Specification

Status: implementation-ready specification — architecture frozen for Phase A
Release target: v1.5.0
Baseline: v1.4.0 — Understand
Theme: Control
Change taxonomy: EVOLUTION / CONTROL / PERSISTENCE / INTEGRATION

## Goal

Turn remaining Codex quota and earned reset credits into explicit, user-controlled operational capacity
without introducing automatic redemption, future-consumption forecasting, or fabricated certainty.

v1.5 SHALL:

1. read current usage and reset-credit state from one supported `account/rateLimits/read` operation;
2. preserve the established `UsageSnapshot` and `UsageProvider` contracts;
3. normalize authoritative reset-credit count plus optional detail coverage;
4. maintain an append-only local event ledger of meaningful reset-credit observations and redemption actions;
5. allow explicit, durable, idempotent manual redemption;
6. monitor known reset-credit expiry facts and produce deterministic control advice;
7. let the user define remaining-quota reserves by stable `UsageWindowId`;
8. preserve all v1.4 GUI lifecycle guarantees.

## Product questions

v1.5 is intended to answer:

- How many earned reset credits are currently available?
- Do I know the details of none, some, or all currently available credits?
- Which known credit expires next?
- Which known credits explicitly do not expire?
- What reset-credit facts has CodexBar observed historically?
- Has CodexBar attempted or confirmed a redeem?
- Is an idempotent redeem attempt currently unresolved?
- Is a known credit approaching expiry?
- How much current quota remains above my configured reserve?
- Is there a deterministic reason to use quota before redeeming, redeem now, or wait for a scheduled reset?

v1.5 SHALL NOT answer:

- when the user will exhaust quota;
- future consumption rate;
- future agent count;
- whether a credit omitted from a partial detail list expired;
- whether every observed positive quota jump is a reset;
- a probabilistic ranking of future usage paths.

## Scoped requirements

- `REQ-RESET-001` — composed current account-rate-limit read and normalized reset-credit inventory.
- `REQ-RESET-LEDGER-001` — append-only reset-credit evidence ledger and projection.
- `REQ-RESET-ACTION-001` — explicit, serialized, idempotent reset-credit redemption process.
- `REQ-RESET-MONITOR-001` — expiry monitoring and deterministic opportunity assessment.
- `REQ-BUDGET-001` — user-defined usage reserve integrated into AppSettings schema v2.

Dependency direction:

`REQ-RESET-001 -> REQ-RESET-LEDGER-001 -> REQ-RESET-ACTION-001`

`REQ-RESET-001 -> REQ-RESET-MONITOR-001`

`REQ-BUDGET-001 -> REQ-RESET-MONITOR-001`

`REQ-RESET-LEDGER-001 -> REQ-RESET-MONITOR-001`

## Stable reset taxonomy

### Scheduled reset

The next reset timestamp reported on a `UsageWindow` (`resets_at`).

It is source metadata about a usage window and remains distinct from a reset credit.

### Reset credit

An earned, redeemable reset capability returned by the supported app-server reset-credit inventory.

`availableCount` is authoritative for the current total. Per-credit rows are supplementary and may be
unavailable or capped.

### Redeem event

An explicit user-approved attempt to consume one reset credit through
`account/rateLimitResetCredit/consume`.

### Observed increase

A factual increase in normalized `remaining` between retained usage observations.

Observed increase is not automatically classified as scheduled reset, banked-reset redemption, grant,
backend correction, or other cause.

## Current state and historical evidence remain separate

Current usage:
- comes from the current supported read or existing v1.4 STALE fallback semantics;
- is not reconstructed from history or the reset ledger.

Current reset-credit inventory:
- comes only from the current supported account-rate-limit read;
- SHALL NOT fall back to the event ledger and call historical evidence current.

Reset event ledger:
- records facts already observed or actions already attempted;
- is append-only evidence;
- supports projections/read models;
- is not an Event Sourcing replacement for current account state.

## Upstream protocol dependency

The specification is based on the Codex app-server contract verified on 2026-08-10.

Required methods:

- `account/rateLimits/read`
- `account/rateLimitResetCredit/consume`

Important upstream semantics:
- one `account/rateLimits/read` response may contain both usage and reset-credit data;
- `availableCount` is authoritative;
- `credits == null` means count-only;
- a returned detail list may be capped;
- each returned credit has mandatory `grantedAt`;
- `expiresAt == null` explicitly means the detailed credit does not expire;
- redemption is caller-idempotent;
- `reset` and `alreadyRedeemed` require authoritative refetch.

See `UPSTREAM-CONTRACT.md`.

## Account read architecture

v1.5 SHALL introduce a composed account-rate-limit observation above the existing usage domain.

Conceptually:

`AccountRateLimitsObservation`
- `usage: UsageSnapshot`
- `reset_credits: ResetCreditReadResult`

`UsageSnapshot` itself SHALL NOT acquire reset-credit fields.

The application ports SHALL follow interface segregation:

- `AccountRateLimitsReader` — read-only account-rate-limit observation.
- `ResetCreditConsumer` — reset-credit side effect.
- existing `UsageProvider` — preserved compatibility interface.

One infrastructure gateway MAY implement both new ports. An adapter SHALL project `UsageSnapshot` for
existing `UsageProvider` consumers.

Normal GUI refresh SHALL use one account-rate-limit read, not separate network polls for usage and reset
credits.

## Account operation serialization

Current refresh, redeem, and post-redeem refetch SHALL be serialized through one logical account-operation
lane.

The application SHALL NOT publish concurrently interleaved account operations that can reorder stale
pre-redeem reads over post-redeem state.

A framework-level actor system is not required; a single-writer command queue/executor is sufficient.

## Persistence compatibility

### Usage history

`history.sqlite3` remains schema 1 and SHALL NOT be migrated by v1.5 reset functionality.

### Reset event ledger

Reset evidence SHALL use an independent database:

`$XDG_DATA_HOME/codexbar/reset-events.sqlite3`

Initial schema version: `1`.

The ledger stores sparse events rather than refresh snapshots and therefore has no automatic retention
requirement in v1.5.

### Settings

v1.5 SHALL intentionally introduce AppSettings persistence schema `2` for per-window reserve policy.

Existing valid schema-1 settings SHALL be migrated in memory to the schema-2 application model.
Reading schema 1 SHALL NOT rewrite the file automatically. The next explicit save SHALL write schema 2.

See ADR-010.

## Event-store philosophy

The reset ledger is an append-only Event Store plus Projection/Read Model, not full Event Sourcing.

Facts include:
- first authoritative count observed;
- subsequent count changes;
- detail-coverage changes;
- detailed credit first observed;
- detailed metadata changes;
- a credit leaving a fully enumerated available set;
- a known expiry deadline passing;
- durable redeem intent;
- typed redeem outcome;
- unresolved/unknown redeem outcome.

The ledger SHALL preserve uncertainty.

## Redeem safety

1. No automatic redemption exists in v1.5.
2. Every new logical redeem requires explicit confirmation.
3. `RedeemAttemptId` SHALL also be the upstream idempotency key.
4. `REDEEM_REQUESTED` SHALL be committed before the first external `consume`.
5. Uncertain retry SHALL reuse the same `RedeemAttemptId`.
6. An unresolved attempt SHALL remain auditable after process restart.
7. Ledger inability to persist the attempt SHALL block redeem.
8. Reset-credit read/monitor failures SHALL not corrupt otherwise valid current usage.
9. Redeem success SHALL never cause an optimistic local 100% quota mutation.
10. Current account state SHALL be refetched after successful/idempotent completion.

## Failure-isolation matrix

| Condition | Current usage | Reset current | Ledger | Redeem | Monitor |
|---|---|---|---|---|---|
| full account read valid | FRESH | CURRENT | process facts | allowed | normal |
| usage valid, optional reset subtree invalid | FRESH | UNAVAILABLE | no new reset facts | blocked | degraded |
| whole upstream read fails | existing v1.4 STALE/error semantics | UNAVAILABLE | no new facts | blocked | degraded |
| ledger unavailable/corrupt | FRESH when usage valid | CURRENT when reset read valid | ERROR | blocked | factual display only |
| consume outcome uncertain | preserve existing usage | unknown until safe refetch | `OUTCOME_UNKNOWN` | retry same ID only | suspended/degraded |
| consume succeeds, refetch fails | existing usage follows normal stale/error semantics | UNAVAILABLE | success retained | attempt terminal | degraded |

## Control philosophy

Control is deterministic policy, not prediction.

For current remaining fraction `R` and configured reserve `R_reserve`:

`headroom = max(R - R_reserve, 0)`

The control policy MAY combine:
- current remaining;
- current reset-credit count/detail coverage;
- known reset-credit expiry;
- scheduled usage-window reset;
- configured reserve/headroom.

It SHALL NOT use recent consumption slope or future workload assumptions.

## v1.5 default control constants

To make behavior testable, v1.5 fixes these policy constants:

- expiry watch horizon: 24 hours;
- expiry urgent horizon: 6 hours;
- scheduled-reset-near horizon: 2 hours;
- meaningful headroom: 5 percentage points.

Only reserve is user-configurable in v1.5.

These constants may become settings in later releases.

## Deferred beyond v1.5

- automatic redeem;
- forecasting / ETA to LOW or exhaustion;
- future agent/workload modeling;
- empirical or Bayesian `R | cycle_progress`;
- probabilistic opportunity ranking;
- causal classification of every observed usage increase;
- remote/cloud ledger;
- account sharing/sync;
- configurable monitor thresholds beyond reserve.

## Required architecture decisions

- ADR-008 — Composed app-server account gateway.
- ADR-009 — Reset event store, projections and redeem process manager.
- ADR-010 — AppSettings schema v2 for control policy.

## Release sequencing

1. freeze reviewed specs, ADRs, task decomposition and traceability;
2. execute Phase A from the frozen implementation plan;
3. introduce composed gateway and compatibility adapter;
4. validate one-read-per-refresh architecture;
5. implement normalized reset inventory;
6. implement reset Event Store + projection + inspection;
7. implement settings schema-v2 migration and reserve policy;
8. implement redeem Process Manager without UI;
9. validate crash/timeout/retry/idempotency recovery;
10. implement factual monitor and deterministic policy;
11. generalize notification transport;
12. integrate Reset/Control UI while preserving v1.4 lifecycle;
13. target validation;
14. release close.

No redeem UI SHALL precede closure of ledger/idempotency semantics.
