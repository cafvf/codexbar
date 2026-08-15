# CodexBar v1.8 — Open Decisions

Status: **no implementation-blocking decisions**

All product-semantic decisions required to begin implementation are closed by `PRODUCT.md`,
`DECISIONS.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md` and ADR-008.

## Resolved during convergence

### OD-1801 — Settings schema-v3 shape

Resolved by DEC-1807/1808 and ADR-008.

Canonical additions are:

- `usage_plan_checkpoints`;
- `plan_breach_notifications_enabled`.

Existing `usage_reserves` remains in place and remains the sole reserve authority.

### OD-1802 — Core Plan result taxonomy

Resolved by DEC-1805.

Use orthogonal checkpoint resolution and compliance concepts rather than one overloaded Plan status.
Exact Python enum/dataclass names may follow the frozen architecture without changing semantics.

### OD-1803 — Budget-to-Plan composition

Resolved: Plan consumes the same canonical reserve policy, not `BudgetViewState` and not a second
reserve field. Budget remains independently evaluable under its released contract.

### OD-1804 — `resets_at < observed_at`

Resolved: factual time-to-reset is invalid for checkpoint resolution. Do not clamp to zero and do not
fabricate a new reset instant. Reserve remains independently usable where applicable.

### OD-1805 — Non-monotonic checkpoint policy

Resolved: structurally valid non-monotonic floors are accepted. v1.8 does not require a feasibility
warning system.

### OD-1806 — Notification rule shape

Resolved: one fixed factual Plan-breach opt-in replaces the earlier generic `notification_rules[]`
concept. No rules engine/DSL is introduced.

### OD-1807 — Shared `TimeToReset` / `FractionDelta`

Resolved: one neutral domain owner with compatibility imports from historical modules.

## Non-blocking implementation choices

The following may be resolved inside tasks while preserving frozen ACs and architecture:

- exact Qt widget arrangement for checkpoint rows;
- whether `PlanPanel` remains in `control_panel.py` or moves to a cohesive small UI module if size/style
  thresholds justify extraction;
- exact factual notification wording;
- formatting of human-friendly checkpoint durations in UI/CLI;
- internal helper names used by schema-v3 codec.

These choices MUST NOT introduce a second settings owner, persistence subsystem, scheduler, cache,
worker, rule engine or History/Context dependency.

## Explicitly deferred maintenance findings

See `COHERENCE-BASELINE.md` for items deliberately kept out of v1.8 unless naturally touched:
startup Settings double-read, redeem enum unification, broad `reset_at` renaming,
`migrated_from_schema_v1` renaming and `CurrentAccountController` removal audit.
