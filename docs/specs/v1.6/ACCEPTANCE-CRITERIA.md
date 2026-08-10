# CodexBar v1.6 — Acceptance Criteria

Status: frozen for implementation

## AC-1601 — Correct contextual coordinate
Given a CURRENT observation with authoritative reset timestamp, Context uses
`reset - observed_at` and does not require nominal window duration.

## AC-1602 — Authoritative cycle identity
Only same-window observations with authoritative historical reset timestamps form
cycles; quota jumps alone never create a cycle.

## AC-1603 — Independent evidence
For any contextual query, each historical cycle contributes at most one value.

## AC-1604 — Current-cycle exclusion
No observation sharing the current cycle identity is included as a historical
comparator.

## AC-1605 — Hybrid tolerance
Eligibility uses exactly `min(0.05*h*, 2h)` and includes the exact boundary.

## AC-1606 — Deterministic tie
Equal mismatch selects later observed_at.

## AC-1607 — Coverage
0–2/3–4/5–9/10+ map to Insufficient/Sparse/Limited/Established exactly.

## AC-1608 — Adaptive statistics
- Insufficient: no distributional summary.
- Sparse: observed min–max.
- Limited: median + observed min–max.
- Established: median + Q25–Q75.
Factual rank/count may appear from Sparse upward.

## AC-1609 — Rank ties
Equal historical values are represented without false strict ordering.

## AC-1610 — 180-day retention
History target retention is 180 days, existing schema-v1 data remain readable,
and cutoff behavior is deterministic.

## AC-1611 — Failure isolation
Context failure does not hide or corrupt Current, History, Control/Budget,
reset-credit state, or manual redeem.

## AC-1612 — Dynamic windows
No production Context logic depends on `window_300m`, `window_10080m`, `5h`,
or `Weekly` identities/labels.

## AC-1613 — No forecast
No v1.6 UI/API emits ETA, predicted remaining, probability of exhaustion,
forecast slope, or predictive interval.

## AC-1614 — No side effects
Context read/evaluation never changes reserves, notifications, reset ledger, or
redeem state.

## AC-1615 — UI clarity
Open Details visually distinguishes authoritative Current from descriptive
Historical Context and always shows comparable-cycle count.

## AC-1616 — Performance evidence
180-day storage/query characterization is recorded before release; schema
evolution is evidence-driven.
