# UC-1709 — Inspect Current window without reserve policy

## Flow
1. Current window has factual remaining quota.
2. No reserve exists for its UsageWindowId.
3. Open Details renders Budget.

## Expected
Remaining is shown; reserve is not set; policy headroom is not applicable.
The UI does not show 0% available merely because policy is absent.
