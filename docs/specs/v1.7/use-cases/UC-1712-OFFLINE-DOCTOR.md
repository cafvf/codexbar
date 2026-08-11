# UC-1712 — Run Doctor without an active GUI

## Flow
1. User runs `codexbar doctor`.
2. CodexBar builds the same health model from offline/local inspections and optional
   read-only probes.
3. Live-only runtime evidence is marked unavailable instead of fabricated.

## Expected
Doctor remains useful without requiring a running GUI process.
