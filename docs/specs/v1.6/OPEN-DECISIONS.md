# CodexBar v1.6 — Open Decisions

Status: no implementation-blocking decisions

The semantic baseline is frozen for implementation.

## Deferred review items

These items MUST NOT block v1.6 implementation, but evidence should be collected
for later review.

### OD-1601 — Tolerance recalibration

Current:

- alpha = 0.05
- delta_h_cap = 2 hours

Review after sufficient real cycles using:

- comparable-cycle inclusion rate;
- exclusion rate by h*;
- polling-cadence distribution;
- sensitivity of median/rank/bands.

### OD-1602 — Coverage threshold recalibration

Current:

- 0–2 Insufficient
- 3–4 Sparse
- 5–9 Limited
- 10+ Established

Review when enough 180-day datasets exist.

### OD-1603 — Retention beyond 180 days

180 days is the v1.6 contract.

Longer retention, compressed cycle summaries, or a dedicated contextual store are
future decisions and require separate evidence.

### OD-1604 — Predictive modeling

Forecasting, probability of exhaustion, and Bayesian/adaptive models remain out of
scope. They require a separate release proposal based on accumulated data.
