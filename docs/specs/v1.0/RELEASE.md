# Release 1.0 — Usable Linux Codex Monitor

## Goal
Deliver a tray application that displays verified Codex usage information safely and refreshes it.

## In scope
REQ-USAGE-001 plus Linux tray presentation, refresh scheduling, stale cache, packaging and smoke tests.

## Out of scope
History/graphs/alerts beyond basic exhausted/low state; developer dashboard; plugin system.

## Release gates
1. Real source contract verified and recorded in ADR-002.
2. Contract fixtures captured with sensitive fields removed.
3. All REQ-USAGE-001 acceptance criteria pass against mock and adapter contract tests.
4. GUI smoke test passes on a supported Linux desktop session.
5. Package starts without requiring development dependencies.
