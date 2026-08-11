# UC-1710 — Read current multi-bucket app-server payload

## Preconditions
Response includes legacy `rateLimits`, explicit `rateLimitsByLimitId.codex`, and
possibly other limit IDs.

## Flow
1. Adapter selects explicit Codex snapshot.
2. It parses its dynamic primary/secondary windows.
3. It ignores unrelated limit IDs.

## Expected
Current represents Codex quota only and remains backward compatible with legacy
fixtures.
