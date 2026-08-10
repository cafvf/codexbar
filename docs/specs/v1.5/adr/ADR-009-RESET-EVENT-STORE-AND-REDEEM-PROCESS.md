# ADR-009 — Reset Event Store, projection and redeem Process Manager

Status: accepted for v1.5 specification

## Context

Reset credits are current external state plus sparse historical facts.
Redeem spans a local durable action and an external idempotent side effect.

Full Event Sourcing would incorrectly make historical events authoritative for current reset inventory.
A naive direct consume call would make timeout/crash ambiguity unsafe.

## Decision

Use:
- independent append-only reset Event Store;
- projection/read model rebuilt from events;
- persisted sequence as authoritative event ordering;
- typed/versioned normalized payloads;
- RedeemAttemptId equal to upstream idempotency key;
- durable REDEEM_REQUESTED before consume;
- Process Manager/Saga-like orchestration;
- serialized account-operation lane.

No general reset-ledger clear in v1.5.

## Consequences

Positive:
- safe retry after ambiguous transport failure;
- auditability;
- explicit uncertainty;
- future probabilistic analysis has provenance-aware events;
- current state remains externally authoritative.

Cost:
- more application orchestration than simple CRUD;
- recovery state must be represented in UI/tests.
