# UC-1706 — Current changes while Context is computing

## Flow
1. Context starts for revisions R1/H.
2. New authoritative Current R2 arrives.
3. A new Context request begins for R2/H.
4. R1/H completes late.
5. Controller rejects obsolete result.

## Expected
UI never regresses to Context calculated for R1.
