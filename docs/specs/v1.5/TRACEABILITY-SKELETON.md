# CodexBar v1.5 — Requirement Traceability Summary

Status: frozen summary; detailed task/test mapping is in TRACEABILITY.md

| Requirement | Use cases | Acceptance criteria | Planned primary boundary |
|---|---|---|---|
| REQ-RESET-001 | UC-RESET-001..005 | AC-RESET-001..020 | composed app-server read -> usage + reset current |
| REQ-RESET-LEDGER-001 | UC-LEDGER-001..006 | AC-LEDGER-001..025 | application event derivation + independent Event Store |
| REQ-RESET-ACTION-001 | UC-REDEEM-001..005 | AC-REDEEM-001..020 | serialized Process Manager + consumer + ledger |
| REQ-RESET-MONITOR-001 | UC-MONITOR-001..006 | AC-MONITOR-001..019 | factual ResetSituation + pure opportunity Strategy |
| REQ-BUDGET-001 | UC-BUDGET-001..004 | AC-BUDGET-001..017 | AppSettings schema v2 + current usage |

## Cross-requirement invariants

- `INV-V15-001`: `UsageSnapshot` remains reset-credit free.
- `INV-V15-002`: usage and reset current originate from one normal account read.
- `INV-V15-003`: current reset inventory never comes from ledger fallback.
- `INV-V15-004`: `availableCount` remains authoritative.
- `INV-V15-005`: `expiresAt=null` for a detailed credit means DOES_NOT_EXPIRE.
- `INV-V15-006`: absence from PARTIAL/COUNT_ONLY detail never confirms removal/expiry/redeem.
- `INV-V15-007`: COMPLETE omission may establish only available-set removal.
- `INV-V15-008`: reset Event Store is historical evidence, not full Event Sourcing.
- `INV-V15-009`: no automatic redeem exists.
- `INV-V15-010`: durable redeem intent precedes side effect.
- `INV-V15-011`: same uncertain logical redeem reuses same attempt/idempotency ID.
- `INV-V15-012`: account operations are serialized.
- `INV-V15-013`: reset monitoring contains no consumption forecast.
- `INV-V15-014`: budget policy does not redefine LOW/EXHAUSTED.
- `INV-V15-015`: history.sqlite3 schema 1 remains unchanged.
- `INV-V15-016`: settings schema 1 is readable/migratable without read-time rewrite.
- `INV-V15-017`: schema-2 settings become canonical on explicit save.
- `INV-V15-018`: raw provider payloads, credentials and account IDs do not cross new persistence boundaries.
- `INV-V15-019`: scheduled reset, reset credit, redeem event and observed increase remain distinct.
- `INV-V15-020`: v1.4 GUI lifecycle/render-on-transition invariants remain protected.

## Architecture decisions

- ADR-008 — composed account gateway.
- ADR-009 — Event Store / projection / redeem process.
- ADR-010 — settings schema v2.
