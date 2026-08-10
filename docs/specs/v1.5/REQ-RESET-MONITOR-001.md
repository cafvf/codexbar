# REQ-RESET-MONITOR-001 — Expiry monitoring and deterministic reset opportunity policy

Status: reviewed draft
Priority: P1
Release: v1.5
Change taxonomy: MONITORING / POLICY / DECISION SUPPORT

## Requirement

CodexBar SHALL separate factual reset situation from deterministic control advice.

It SHALL monitor known expiry facts and derive opportunity classifications using only current factual state,
known event evidence, scheduled reset metadata, fixed v1.5 thresholds and user reserve policy.

No consumption forecast is permitted.

## ResetSituation

A factual application read model containing only known/current inputs required by control, including as
available:

- authoritative reset `available_count`;
- detail coverage;
- known expiring detailed credits;
- known explicitly non-expiring credits;
- selected/current usage window remaining;
- selected/current usage window scheduled reset;
- configured reserve/headroom;
- unresolved redeem state.

It SHALL preserve missing/incomplete fields rather than substitute ledger/history as current data.

## ResetOpportunityPolicy

A pure Strategy/Policy receives a `ResetSituation` and returns a deterministic assessment.

v1.5 fixed constants:

- `EXPIRY_WATCH_HORIZON = 24h`
- `EXPIRY_URGENT_HORIZON = 6h`
- `SCHEDULED_RESET_NEAR_HORIZON = 2h`
- `MEANINGFUL_HEADROOM = 0.05` (5 percentage points)

Only usage reserve is user-configurable in v1.5.

## Policy vocabulary

`NO_ACTION`
- no stronger condition is satisfied.

`EXPIRY_WATCH`
- at least one known expiring credit is within 24h;
- stronger urgent/action condition is not satisfied.

`USE_BEFORE_REDEEM`
- at least one known expiring credit is within 6h;
- configured headroom for the assessed usage window is at least 5 percentage points;
- scheduled reset is known and more than 2h away;
- no unresolved redeem attempt blocks advice.

Meaning:
there is current discretionary quota that could be productively used before spending a soon-expiring credit.

`REDEEM_AVAILABLE`
- authoritative `available_count > 0`;
- current remaining is at or below configured reserve;
- scheduled reset is known and more than 2h away;
- no unresolved redeem attempt.

Expiry need not be known for generic redeem availability.

`WAIT_FOR_SCHEDULED_RESET`
- authoritative `available_count > 0`;
- scheduled reset is known and within 2h;
- scheduled reset is preferred over spending a banked reset under v1.5 policy.

`DATA_INCOMPLETE`
- no higher-priority safe factual classification can be produced because required current reset/current
  usage/control data are unavailable.

Priority when multiple conditions hold:

1. unresolved redeem -> `DATA_INCOMPLETE` / recovery UI;
2. `WAIT_FOR_SCHEDULED_RESET`;
3. `REDEEM_AVAILABLE`;
4. `USE_BEFORE_REDEEM`;
5. `EXPIRY_WATCH`;
6. `NO_ACTION`.

Exact UI wording is not part of the pure policy.

## Factual notifications

Monitor MAY generate deduplicated fact notifications:

- new detailed credit discovered;
- available count changed;
- known expiring credit enters 24h;
- known expiring credit enters 6h;
- known expiring credit enters 1h;
- known expiry deadline passed.

`expiresAt == null` (DOES_NOT_EXPIRE) SHALL never generate expiry alerts.

COUNT_ONLY/PARTIAL unknown identities SHALL not generate fabricated expiry alerts.

## Notification boundary

v1.5 SHALL generalize notification transport away from usage-specific `AlertEvent`.

Infrastructure notification adapter SHOULD accept a transport-neutral message such as:
- summary;
- body;
- urgency.

Usage alert and reset monitor services SHALL independently map their domain/application events into that
message.

## Use cases

### UC-MONITOR-001 — Known expiry

Detailed credit expires in 5h -> factual urgent expiry state exists.

### UC-MONITOR-002 — Non-expiring credit

Detailed credit explicitly has no expiry -> no expiry countdown/warning.

### UC-MONITOR-003 — Count only

Three resets available, no details -> count is shown; no per-credit expiry fabricated.

### UC-MONITOR-004 — Use-before-redeem opportunity

Known credit expires in 4h, weekly remaining 35%, configured reserve 15%, scheduled weekly reset in 2d.

Headroom 20pp -> `USE_BEFORE_REDEEM`.

### UC-MONITOR-005 — Redeem available

Remaining is 10%, reserve 15%, count > 0, scheduled reset in 1d -> `REDEEM_AVAILABLE`.

### UC-MONITOR-006 — Wait

Scheduled reset in 90 min and a reset credit is available -> `WAIT_FOR_SCHEDULED_RESET`.

## Acceptance criteria

- `AC-MONITOR-001`: facts and policy outputs are separate types/services.
- `AC-MONITOR-002`: policy is pure/deterministic for equal inputs.
- `AC-MONITOR-003`: fixed thresholds exactly match release constants.
- `AC-MONITOR-004`: no expiry alert without concrete EXPIRES_AT.
- `AC-MONITOR-005`: DOES_NOT_EXPIRE never receives expiry countdown.
- `AC-MONITOR-006`: COUNT_ONLY/PARTIAL missing detail never fabricates expiry.
- `AC-MONITOR-007`: horizons use timezone-aware instants.
- `AC-MONITOR-008`: each credit/horizon factual alert is deduplicated.
- `AC-MONITOR-009`: deadline-passed is not presented as confirmed expiry by itself.
- `AC-MONITOR-010`: opportunity policy uses no recent slope/rate/forecast.
- `AC-MONITOR-011`: USE_BEFORE_REDEEM requires urgent known expiry + >=5pp headroom + scheduled reset >2h.
- `AC-MONITOR-012`: REDEEM_AVAILABLE requires count>0 + remaining<=reserve + scheduled reset >2h.
- `AC-MONITOR-013`: WAIT_FOR_SCHEDULED_RESET requires count>0 + scheduled reset<=2h.
- `AC-MONITOR-014`: advice never triggers automatic code execution or redeem.
- `AC-MONITOR-015`: scheduled reset and banked reset remain distinct vocabulary.
- `AC-MONITOR-016`: missing required current facts degrades explicitly.
- `AC-MONITOR-017`: unresolved redeem prevents ordinary action advice until recovery is resolved.
- `AC-MONITOR-018`: reset notifications and existing usage alerts can share transport without sharing
  domain event types.
- `AC-MONITOR-019`: monitor adds no second independent app-server polling scheduler.

## Deferred

Probabilistic opportunity ranking and learned usage behavior belong to v1.6+.

## Implementation mapping

Primary task range: `TASK-550..559`.
Detailed AC-to-task/test mapping: `TRACEABILITY.md`.
