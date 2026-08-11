# CodexBar v1.7 — Upstream Codex Contract Evidence

Status: frozen evidence baseline
Evidence review date: 2026-08-10

This document records only supported/public Codex app-server surfaces used to
constrain v1.7 design. CodexBar must not depend on private backend endpoints or
private token-storage structure for product behavior.

## 1. App-server lifecycle

Supported app-server communication is JSON-RPC-like and requires one
`initialize` request plus `initialized` notification per transport connection
before ordinary requests.

CodexBar v1.6 currently uses a one-shot stdio lifecycle per operation.

v1.7 keeps one-shot as the default until characterization demonstrates that a
persistent supervised session materially justifies extra lifecycle complexity.

## 2. Account state

Supported `account/read` can return a ChatGPT account with:

- `type`;
- nullable `email`;
- `planType`.

The supported response does not expose a stable opaque `accountId`.

Upstream auth internals may contain ChatGPT user/account identifiers, but those
are not part of the supported `account/read` response contract.

### v1.7 consequence

CodexBar MUST NOT:

- decode private JWT claims for lineage;
- read private `auth.json` structure for lineage;
- persist an undocumented internal account ID.

The v1.7 History contract is explicitly single-account/local-auth-environment.

## 3. Rate-limit state

`account/rateLimits/read` remains the supported snapshot boundary for current
ChatGPT rate limits and reset-credit state.

Current protocol generation also exposes:

- legacy `rateLimits`, described as a backward-compatible single-bucket view;
- `rateLimitsByLimitId`, a multi-bucket view keyed by metered limit ID.

### v1.7 consequence

When an explicit `codex` entry exists in `rateLimitsByLimitId`, CodexBar treats
that snapshot as the authoritative Codex rate-limit snapshot.

Otherwise CodexBar falls back to the compatible legacy `rateLimits` snapshot.

The parser must continue to support dynamic quota-window durations.

## 4. Reset-credit mutation

`account/rateLimitResetCredit/consume` remains the supported destructive boundary.

v1.7 preserves:

- caller-provided idempotency key;
- optional opaque credit ID;
- refetch after successful/idempotent-success consume;
- no inferred state mutation.

## 5. Contract drift policy

Protocol compatibility MUST be tested using explicit fixtures.

Unknown/unsupported shape must fail safely into existing normalized source/schema
errors instead of fabricating usage.

Source-contract changes discovered during v1.7 implementation require a documented
spec amendment before semantic behavior changes.
