# UC-1609 — Missing reset metadata

## Scenario
Current or historical observations do not have authoritative `resets_at`.

## Expected behavior
- missing current reset -> Context unavailable for that window;
- missing historical reset -> those historical observations are ineligible;
- no reset boundary is inferred from remaining-quota jumps.
