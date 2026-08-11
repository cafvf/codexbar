# CodexBar v1.6 — Integration Hygiene Review

Status: implementation review before Phase F
Baseline: `28f9460` plus Integration Hardening changes

## Objective

Reduce cross-version integration complexity while preserving all validated v1.4/v1.5/v1.6 behavior.
The review treats three state axes as independent concepts:

- **freshness**: whether current account data are authoritative now (`CURRENT` / `STALE`);
- **availability**: whether an optional subsystem can provide its result;
- **coverage**: how much independent historical evidence supports Context.

No one axis should be used as a fallback representation for another.

## Simplifications and corrections

1. `composition.py` no longer relies on branch-local union inference for Context repositories.
   Each History branch builds its final `HistoricalContextService` directly.
2. Current observation invalidation now applies to every `UsageError`, including parse/schema failures,
   not only transport/source failures.
3. The legacy `CurrentAccountController` uses the same invalidation taxonomy for consistency.
4. Stale usage remains visible as stale Current, but Control/Budget is withheld instead of being
   recomputed from stale data.
5. Reset Current becomes unavailable after a failed account read; reset-ledger projection is never used
   as a replacement for Current reset state.
6. Context remains unavailable when Current is stale and does not query History in that state.
7. `HistoricalContextResult` validation uses explicit state rules rather than boolean-equivalence logic.
8. History availability, Reset Ledger availability and Context coverage remain independent axes.
9. Redeem remains fail-closed when durable reset-ledger state is unavailable.
10. Previously introduced storage-contract validation, generation-based refresh invalidation,
    centralized retention and explicit Context wiring remain intact.

## Taxonomy decisions

### Usage freshness

`Freshness.CURRENT` means the observation came from the latest successful authoritative read.
Any failed account read invalidates Current-derived reset/control/context state even when the last usage
value remains displayable as stale.

### Optional subsystem availability

History and Reset Ledger may be unavailable without making Current usage unavailable. Their failures
must degrade only dependent features.

### Context evidence coverage

`ContextCoverage` only describes independent-cycle evidence quantity. It does not describe repository
availability or Current freshness.

### Opportunity priority

`OpportunityPriority.NONE` remains a policy result, not a general availability state. UI surfaces must
use Current freshness/subsystem failure information when deciding whether control output is withheld.

## Regression focus

The integration tests cover:

- source failure -> stale composed observation;
- schema/parse failure -> stale composed observation;
- stale Current -> no Context History I/O;
- stale Current -> no Control/Budget calculation;
- expired reset credit -> no upcoming-expiry opportunity;
- post-command snapshot -> older asynchronous refresh result discarded;
- History/Reset SQLite operational-contract validation.

The full protected baseline remains authoritative and must be run after applying this package.
