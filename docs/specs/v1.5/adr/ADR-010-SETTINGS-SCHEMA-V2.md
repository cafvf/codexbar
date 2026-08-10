# ADR-010 — AppSettings schema v2 for usage reserve policy

Status: accepted for v1.5 specification

## Context

Usage reserve is application behavior/configuration.

Creating a second `control-policy.json` would create two configuration sources and duplicate persistence
lifecycle already solved by `AppSettings`.

The existing JSON settings codec is explicitly schema-versioned and atomic.

## Decision

Extend canonical `AppSettings` with per-UsageWindowId reserves and introduce settings persistence schema 2.

Migration:
- valid schema 1 is accepted;
- in-memory application model receives empty reserves;
- read alone does not rewrite disk;
- next explicit save writes canonical schema 2.

## Consequences

Positive:
- one source of truth for user-configurable behavior;
- existing settings UI/runtime application pattern can be extended;
- migration is explicit and testable.

Cost:
- v1.5 must add a real settings migration path instead of continuing strict single-version decode.
