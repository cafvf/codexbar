# UC-1702 — Diagnose degraded capability

## Preconditions
At least one non-destructive subsystem is unavailable or Current is stale.

## Flow
1. User runs Doctor or opens System Health.
2. Healthy components remain visible.
3. Failed/degraded component has an explicit diagnostic.
4. Overall status follows frozen derivation rules.

## Expected
One failed optional subsystem does not erase unrelated healthy evidence.
