# CodexBar v1.6 — Specification Review Checklist

## Semantics
- [x] time-to-reset coordinate accepted.
- [x] 180-day retention accepted.
- [x] independent cycle is evidence unit.
- [x] hybrid tolerance accepted.
- [x] alpha=0.05 accepted as initial heuristic.
- [x] delta_h_cap=2h accepted as initial heuristic.
- [x] coverage thresholds accepted provisionally.
- [x] adaptive statistical presentation accepted.
- [x] no forecasting in v1.6.

## Determinism
- [x] current cycle excluded.
- [x] one observation per cycle.
- [x] equal-distance tie rule defined.
- [x] rank ties defined.
- [x] quantile convention defined.
- [x] timezone-aware UTC arithmetic required.

## Architecture
- [x] schema-v1 first strategy.
- [x] no separate Context database initially.
- [x] no Current-state substitution.
- [x] failure isolation required.
- [x] Context UI separate from tray/History/Control.
- [x] no Context-driven alerts.

## Implementation readiness
- [x] use cases written.
- [x] acceptance criteria written.
- [x] P0 traceability written.
- [x] canonical test vectors written.
- [x] phases and tasks written.
- [x] every phase has a gate.
- [x] no blocking open decision remains.

Result: READY FOR IMPLEMENTATION AFTER SPEC COMMIT.
