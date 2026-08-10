# CodexBar v1.5 — Open Decisions

Status: no implementation-blocking architectural decisions

## Frozen decisions

1. `UsageSnapshot` remains unchanged.
2. One normal account read supplies usage and reset-credit state.
3. `availableCount` is authoritative.
4. `expiresAt=null` on a detailed credit means DOES_NOT_EXPIRE.
5. Reset Event Store is historical evidence, not current-state Event Sourcing.
6. Reset ledger uses independent SQLite schema v1.
7. General ledger clear is not exposed in v1.5.
8. `RedeemAttemptId` equals the upstream idempotency key.
9. account refresh/redeem/refetch operations are serialized.
10. no automatic redeem.
11. AppSettings moves to persistence schema v2 with read-time in-memory migration from schema 1.
12. only reserve is user-configurable among new Control thresholds.
13. notification transport becomes domain-neutral.
14. v1.4 GUI lifecycle remains protected.

## Non-blocking implementation choices

These may be resolved inside tasks without changing product semantics:

- exact Python module names for reset value types;
- whether `AccountRateLimitsObservation` lives in `application/account.py` or an equivalent cohesive module;
- whether the single account-operation lane reuses the existing controller executor or a dedicated
  application coordinator abstraction;
- exact versioned JSON payload shape inside reset Event Store, provided event semantics and schema tests hold;
- exact visual placement of ResetCreditsPanel and BudgetPanel within Current Details;
- exact wording of confirmation/notification text, subject to factual/policy distinction.

Changing any frozen decision requires a spec/ADR update before code.
