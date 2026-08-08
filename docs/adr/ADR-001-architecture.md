# ADR-001 — Lightweight hexagonal core with presentation ViewModel

Status: accepted

## Decision
Use a small ports-and-adapters architecture. Domain models and application use cases are framework-free.
Infrastructure implements the `UsageProvider` port. Presentation maps snapshots to view state; Qt is a
shell around that state.

## Rejected
- Four-layer enterprise architecture: unnecessary ceremony for this utility.
- Event bus/plugin architecture in v1: speculative complexity.
- UI calling Codex directly: untestable coupling to a volatile source.

## Consequence
A future source can be replaced without changing domain/UI contracts, while the project remains small.
