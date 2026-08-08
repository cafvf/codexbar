# ADR-002 — Production Codex usage source

Status: **accepted**  
Date: 2026-08-08

## Context
CodexBar requires structured, local, authenticated usage data. Parsing `/status` text would couple the
product to terminal presentation and is explicitly disfavored by C-07.

## Decision
Use the stable `codex app-server` JSON-RPC stdio interface and call `account/rateLimits/read` after the
required `initialize` / `initialized` handshake.

The adapter maps only documented fields required by REQ-USAGE-001:

- `usedPercent` -> `remaining = (100 - usedPercent) / 100`;
- `windowDurationMins` -> opaque domain id plus human-readable label;
- `resetsAt` -> timezone-aware UTC `datetime`;
- `rateLimitReachedType` -> opaque backend classification.

`primary` and `secondary` are not domain concepts. Their duration determines identity; either may be
null and neither is synthesized.

## Consequences
- No scraping of TUI prose.
- Codex must be locally installed and authenticated for production usage.
- The adapter is version-sensitive only at one isolated boundary and fails closed on malformed schema.
- App-server notifications can support live updates later, but v1.0 reads snapshots on demand.

## Evidence
OpenAI's Codex app-server documentation describes newline-delimited JSON over stdio, the mandatory
initialization handshake, and `account/rateLimits/read` with `usedPercent`, `windowDurationMins`, and
`resetsAt`.
