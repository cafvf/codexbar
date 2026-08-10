# UC-1601 — Inspect historical context for current usage

## Actor
CodexBar user.

## Preconditions
- a CURRENT usage observation exists;
- the selected window has `resets_at`;
- history repository is readable.

## Main flow
1. User opens Current Details.
2. CodexBar identifies the current `UsageWindowId`.
3. CodexBar calculates `h* = resets_at - observed_at`.
4. CodexBar queries up to 180 days of eligible history for that window.
5. Observations are grouped by `(UsageWindowId, historical resets_at)`.
6. The current cycle is excluded.
7. One nearest real observation is selected per previous cycle.
8. Hybrid tolerance is applied.
9. Coverage is classified from the final cycle count.
10. Statistics allowed by that coverage class are calculated.
11. Historical Context renders the result.

## Success
The user can see how current remaining quota compares with independent historical
cycles without receiving a forecast.

## Alternate flows
- no current reset timestamp -> Context unavailable with factual reason;
- no comparable cycles -> Insufficient;
- history failure -> Context unavailable, Current remains healthy.
