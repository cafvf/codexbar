# UC-1704 — Recover a stale instance endpoint

## Preconditions
A prior GUI crashed and left a local endpoint, but no live owner responds.

## Flow
1. New GUI launch tests endpoint liveness.
2. Liveness fails.
3. CodexBar safely removes/reclaims stale endpoint.
4. New process becomes owner.

## Expected
No manual file cleanup is required and no competing owner is created.
