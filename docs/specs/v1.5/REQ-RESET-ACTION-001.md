# REQ-RESET-ACTION-001 — Explicit serialized idempotent redemption

Status: reviewed draft
Priority: P0
Release: v1.5
Change taxonomy: USER ACTION / SIDE EFFECT / PROCESS MANAGER

## Requirement

CodexBar SHALL allow explicit reset-credit redemption through the supported
`account/rateLimitResetCredit/consume` method.

Redemption SHALL be coordinated by a durable Process Manager/Saga-like workflow and serialized with account
refresh operations.

No automatic redemption exists in v1.5.

## RedeemAttemptId

Each new logical redeem attempt SHALL receive one UUID-like `RedeemAttemptId`.

The exact same value SHALL be used as:
- local logical attempt identity;
- upstream `idempotencyKey`.

A retry of the same uncertain logical attempt reuses it.
A distinct new user-approved attempt receives a new ID.

## Process states

Minimum logical states:

`REQUESTED`
- durable intent exists before external send.

Terminal known states:
- `SUCCEEDED`;
- `ALREADY_SUCCEEDED`;
- `NOTHING_TO_RESET`;
- `NO_CREDIT`.

Non-terminal/recoverable state:
- `OUTCOME_UNKNOWN`.

Implementation SHALL derive these from ledger events rather than store an unrelated mutable source of truth.

## Process order

1. user explicitly invokes redeem;
2. confirmation is shown;
3. new `RedeemAttemptId` is created;
4. `REDEEM_REQUESTED` is committed;
5. only after commit may `consume` be sent;
6. typed upstream outcome is persisted;
7. successful/idempotent completion triggers fresh `account/rateLimits/read`;
8. resulting current state follows normal current-state publication/capture rules.

If the external outcome cannot be established after a request may have been sent:
- persist `REDEEM_OUTCOME_UNKNOWN`;
- do not assume success/failure;
- allow safe retry with the same attempt ID.

## Account-operation serialization

Refresh, redeem and post-redeem refetch SHALL run through one logical account-operation lane.

A refresh SHALL NOT race a redeem such that a pre-redeem account snapshot can be published after the
post-redeem result.

Repeated UI activation SHALL not enqueue concurrent logical redeems.

## Credit selection

Known detailed credit selected:
- send that opaque `creditId`.

Count-only or no selectable detail:
- generic redeem MAY omit `creditId`;
- UI SHALL state backend selection is opaque;
- CodexBar SHALL NOT claim earliest-expiring selection.

## Outcomes

`reset`
- append `REDEEM_SUCCEEDED`;
- attempt terminal successful;
- authoritative refetch required.

`alreadyRedeemed`
- append `REDEEM_ALREADY_SUCCEEDED`;
- attempt terminal idempotent successful;
- authoritative refetch required.

`nothingToReset`
- append `REDEEM_NOTHING_TO_RESET`;
- no optimistic mutation.

`noCredit`
- append `REDEEM_NO_CREDIT`;
- no optimistic mutation.

Transport/process ambiguity:
- append `REDEEM_OUTCOME_UNKNOWN`;
- retain same attempt ID for retry.

## Startup recovery

If projection contains unresolved `REQUESTED` or `OUTCOME_UNKNOWN` attempts:
- UI SHALL surface recovery state;
- CodexBar SHALL not silently create a new attempt to replace them;
- user may explicitly retry the same attempt ID or abandon recovery if a later reviewed rule permits it.

v1.5 SHALL specify/implement retry; destructive abandonment may be deferred if not required.

## Use cases

### UC-REDEEM-001 — Selected credit

Explicit selected-credit redeem completes and refetches.

### UC-REDEEM-002 — Generic count-only redeem

User knowingly asks backend to select a reset credit.

### UC-REDEEM-003 — Timeout after possible send

Outcome becomes unknown and same attempt ID is reused.

### UC-REDEEM-004 — Crash after REQUESTED before send

On restart the durable attempt exists; replay/retry with same ID remains safe.

### UC-REDEEM-005 — Already redeemed retry

`alreadyRedeemed` closes the attempt successfully and refetches.

## Acceptance criteria

- `AC-REDEEM-001`: no automatic redeem path exists.
- `AC-REDEEM-002`: every new logical attempt requires explicit user confirmation.
- `AC-REDEEM-003`: attempt ID equals upstream idempotency key.
- `AC-REDEEM-004`: `REDEEM_REQUESTED` is committed before first external send.
- `AC-REDEEM-005`: persistence failure prevents the side effect.
- `AC-REDEEM-006`: uncertain retry reuses the same attempt ID.
- `AC-REDEEM-007`: distinct confirmed action uses a new attempt ID.
- `AC-REDEEM-008`: selected known credit ID is passed opaquely.
- `AC-REDEEM-009`: generic redeem never invents which credit backend selected.
- `AC-REDEEM-010`: documented outcomes map to typed application outcomes/events.
- `AC-REDEEM-011`: reset/alreadyRedeemed require fresh composed account read.
- `AC-REDEEM-012`: nothingToReset/noCredit cause no optimistic local mutation.
- `AC-REDEEM-013`: possible-send ambiguity is represented as OUTCOME_UNKNOWN.
- `AC-REDEEM-014`: unresolved attempts survive restart.
- `AC-REDEEM-015`: account refresh and redeem operations are serialized.
- `AC-REDEEM-016`: pre-redeem refresh cannot overwrite newer post-redeem current state.
- `AC-REDEEM-017`: double click cannot bypass confirmation/create concurrent logical redeems.
- `AC-REDEEM-018`: redeem error does not terminate GUI event loop.
- `AC-REDEEM-019`: consume success plus refetch failure keeps terminal action evidence while current reset
  state degrades independently.
- `AC-REDEEM-020`: raw credentials/account identifiers are not persisted/logged by the redeem workflow.

## Protected invariants

Redeem is a secondary account side effect. Existing history capture, usage classification and v1.4 GUI
lifecycle SHALL not be redefined by this requirement.

## Implementation mapping

Primary task range: `TASK-540..549`.
Detailed AC-to-task/test mapping: `TRACEABILITY.md`.
