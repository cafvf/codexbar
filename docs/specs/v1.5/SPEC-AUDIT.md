# CodexBar v1.5 — Specification Audit

Status: implementation-ready audit

Acceptance criteria discovered: 101.

## Acceptance-criterion families

- `BUDGET`: 001..017 (17 criteria)
- `LEDGER`: 001..025 (25 criteria)
- `MONITOR`: 001..019 (19 criteria)
- `REDEEM`: 001..020 (20 criteria)
- `RESET`: 001..020 (20 criteria)

All five requirement families are mapped by explicit AC ranges in `TRACEABILITY.md`.

## Blocking decisions

None. See `OPEN-DECISIONS.md`.

## Deliberate deferrals

- automatic redeem;
- forecasting/ETA;
- probabilistic cycle model;
- reset-ledger general clear;
- configurable monitor thresholds beyond reserve;
- remote/cloud persistence.

## Implementation start

The first code task is `TASK-510`. No production redeem UI is permitted before Gate D passes.
