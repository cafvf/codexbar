# UC-1611 — 180-day retention

## Scenario
History maintenance runs with observations older than, equal to, and newer than
the 180-day cutoff.

## Expected behavior
- observations outside retention are pruned according to frozen cutoff semantics;
- cutoff calculation uses one captured reference instant;
- schema-v1 database remains readable;
- existing History queries remain correct.
