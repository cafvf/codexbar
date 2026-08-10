# ADR-008 — Composed account-rate-limit gateway

Status: accepted for v1.5 specification

## Context

The existing `UsageProvider` returns only `UsageSnapshot`, while the same supported
`account/rateLimits/read` response now contains both usage and optional reset-credit state.

Adding reset credits to `UsageSnapshot` would mix distinct domain concepts.
Polling reset credits separately would duplicate network work and create synchronization races.

## Decision

Introduce:
- `AccountRateLimitsReader` read port;
- `ResetCreditConsumer` side-effect port;
- `AccountRateLimitsObservation` application DTO;
- `CodexAppServerGateway` infrastructure implementation;
- compatibility `UsageProvider` adapter.

One normal refresh uses one composed read.

## Consequences

Positive:
- UsageSnapshot remains stable.
- Existing CLI/mocks/use cases can keep UsageProvider.
- reset and usage timestamps derive from one read boundary.
- no second poll scheduler.
- destructive capability is interface-segregated.

Cost:
- provider infrastructure must be refactored before reset UI.
- composition root becomes more explicit.
