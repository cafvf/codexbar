# UC-1701 — Inspect a healthy CodexBar

## Actor
User or developer.

## Preconditions
Codex source is readable; local stores are healthy; GUI may or may not be running.

## Flow
1. User runs `codexbar doctor`.
2. CodexBar performs read-only local inspection and allowed probes.
3. It builds one SystemHealthSnapshot.
4. It renders component states and overall health.

## Expected
- overall status is healthy;
- evidence origins are factual;
- no state changes occur;
- Context insufficient coverage, if present, is not mislabeled as an application
  failure.
