# UC-1705 — Re-render Context without new evidence

## Preconditions
CurrentRevision R and HistoryRevision H already produced Context for window W.

## Flow
1. UI requests Context again for R/H/W.
2. Controller finds cache entry.
3. Equal application result is returned without repository/full summary work.

## Expected
Semantic result is identical and cache-hit performance budget is met.
