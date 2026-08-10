# REQ-RESET-001 — Composed current account read and reset-credit inventory

Status: reviewed draft
Priority: P0
Release: v1.5
Change taxonomy: EVOLUTION / PROVIDER / DOMAIN / INTEGRATION

## Requirement

CodexBar SHALL obtain current usage and current reset-credit information from one supported
`account/rateLimits/read` operation and normalize them into separate stable concepts.

`UsageSnapshot` SHALL remain unchanged.

The application SHALL expose a composed account observation above usage:

`AccountRateLimitsObservation`
- `usage: UsageSnapshot`
- `reset_credits: ResetCreditReadResult`

## Application ports

Interface segregation is normative.

### AccountRateLimitsReader

Read-only port returning the composed current observation.

### ResetCreditConsumer

Side-effect port accepting a normalized consume command and returning a typed consume outcome.

### UsageProvider

Existing compatibility port remains valid.

A `UsageProvider` adapter MAY project `observation.usage` from `AccountRateLimitsReader`.

No read-only service SHALL require access to the destructive consumer port.

## ResetCreditReadResult

At minimum represents:
- `CURRENT(inventory)`;
- `UNAVAILABLE(diagnostic?)`.

A prior ledger projection SHALL NOT be substituted for CURRENT inventory.

## ResetCreditInventory

Contains:
- timezone-aware `observed_at`;
- authoritative non-negative `available_count`;
- `detail_coverage`;
- zero or more normalized detailed credits.

## Detail coverage

`COUNT_ONLY`
- `credits == null`.

`DETAILS_PARTIAL`
- detail array returned;
- unique detail count is less than `available_count`.

`DETAILS_COMPLETE`
- detail array returned;
- unique detail count equals `available_count`.

`n_details > available_count` is inconsistent and fails reset-detail normalization safely.

`rateLimitResetCredits == null` is represented by `ResetCreditReadResult.UNAVAILABLE`, not by an inventory
with zero count.

## ResetCreditDetail

Contains:
- opaque non-empty `credit_id`;
- source reset type;
- source status;
- mandatory timezone-aware `granted_at`;
- explicit expiry knowledge;
- optional display title/description.

## Expiry knowledge

The normalized model SHALL distinguish:

`EXPIRES_AT(datetime)`
- source returned a concrete `expiresAt`.

`DOES_NOT_EXPIRE`
- detailed credit returned `expiresAt == null`.

`UNKNOWN`
- only valid when no detail exists for that inventory item; it is not a property of a returned detailed
  credit.

## Use cases

### UC-RESET-001 — Count only

Backend reports `availableCount=3`, `credits=null`.

CodexBar presents three available resets and explicitly states that per-credit identity/expiry detail is
unavailable.

### UC-RESET-002 — Partial details

Backend reports count 4 and two unique detail rows.

CodexBar presents count 4, coverage `DETAILS_PARTIAL`, and only the two known details.

### UC-RESET-003 — Complete details

Backend reports count 2 and exactly two unique detail rows.

CodexBar can treat absence of previously known detailed IDs from a later COMPLETE inventory as meaningful
available-set evidence for the ledger.

### UC-RESET-004 — Non-expiring credit

A returned detailed credit has `expiresAt=null`.

CodexBar represents it as explicitly non-expiring.

### UC-RESET-005 — Reset capability unavailable

Usage is valid but reset-credit data are absent/invalid in an isolatable optional subtree.

Current usage remains valid while reset state is unavailable.

## Acceptance criteria

- `AC-RESET-001`: usage and reset credits originate from the same normal account read.
- `AC-RESET-002`: `UsageSnapshot` gains no reset-credit fields.
- `AC-RESET-003`: existing `UsageProvider` remains a supported compatibility interface.
- `AC-RESET-004`: `availableCount` normalizes to a non-negative integer and remains authoritative.
- `AC-RESET-005`: `rateLimitResetCredits == null` is not normalized to zero available resets.
- `AC-RESET-006`: `credits == null` produces `COUNT_ONLY`.
- `AC-RESET-007`: unique detail count below authoritative count produces `DETAILS_PARTIAL`.
- `AC-RESET-008`: unique detail count equal to authoritative count produces `DETAILS_COMPLETE`.
- `AC-RESET-009`: detail count above authoritative count fails reset-detail normalization.
- `AC-RESET-010`: duplicate detailed credit IDs fail reset-detail normalization safely.
- `AC-RESET-011`: `credit_id` remains opaque and non-empty.
- `AC-RESET-012`: returned `grantedAt` is mandatory and normalized to timezone-aware UTC.
- `AC-RESET-013`: concrete `expiresAt` becomes `EXPIRES_AT`.
- `AC-RESET-014`: returned `expiresAt == null` becomes `DOES_NOT_EXPIRE`.
- `AC-RESET-015`: UI does not show unknown expiry for a credit explicitly known not to expire.
- `AC-RESET-016`: unknown/future source reset-type/status values do not corrupt current usage parsing.
- `AC-RESET-017`: current reset state never comes from ledger fallback.
- `AC-RESET-018`: malformed reset detail, when isolatable, degrades reset state without fabricating whole
  usage-source failure.
- `AC-RESET-019`: normal GUI refresh introduces no second independent reset polling scheduler.
- `AC-RESET-020`: raw payloads, auth credentials and account IDs do not enter the normalized domain.

## Protected invariants

Existing usage parsing, `Freshness`, history capture, UsagePolicy, alerts and v1.4 lifecycle semantics remain
unchanged unless another reviewed v1.5 requirement explicitly changes a cross-cutting port.

## Implementation mapping

Primary task range: `TASK-510..519`.
Detailed AC-to-task/test mapping: `TRACEABILITY.md`.
