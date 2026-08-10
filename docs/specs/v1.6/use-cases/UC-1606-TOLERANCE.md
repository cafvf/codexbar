# UC-1606 — Exclude non-comparable cycle position

## Scenario
Current h* is known, but a historical cycle's nearest observation lies outside:

    min(0.05 * h*, 2 hours)

## Expected behavior
That cycle contributes no value to the reference set.

No interpolation or nearest-outside-tolerance fallback is permitted.
