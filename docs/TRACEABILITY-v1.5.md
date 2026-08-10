# CodexBar v1.5 Traceability Closure

Status: **CLOSED**

All mandatory Phase A-G release criteria are implemented and validated.

| Phase | Capability | Automated evidence | Target evidence | Status |
|---|---|---|---|---|
| A | composed account gateway | account parser/provider/phase-A tests | real current-state behavior | PASS |
| B | reset event ledger | reset SQLite/derivation/projection tests | ledger inspection path | PASS |
| C | settings v2 + budget | schema migration/schema-v2/budget tests | reserve save/apply, zero-remaining case | PASS |
| D | redeem process | process/retry/recovery/ordering tests | explicit confirmation surface | PASS |
| E | monitor + notifications | opportunity/expiry/failure tests | target notification/control behavior | PASS |
| F | UI integration | reset/budget/redeem/lifecycle tests | physical Current/History/control checks | PASS |
| G | release validation | validation-script/release-metadata tests | full target validation | PASS |

## Closed P0 invariants

- `UsageSnapshot` contains no reset-credit state.
- legacy `UsageProvider` compatibility remains intact.
- usage history remains schema 1 and CURRENT-only.
- History lifecycle remains functional.
- LOW/EXHAUSTED semantics remain protected.
- settings schema 1 remains readable.
- settings schema 2 persists reserves by stable `UsageWindowId`.
- reserve UI does not assume fixed quota-window identities.
- no automatic redeem exists.
- redeem is disabled when no current reset credit is available.
- destructive retries reuse the original idempotency key.
- ambiguous consume outcomes remain recoverable.
- monitor/policy does not forecast from history.
- native indicator / Qt fallback contract remains protected.

## Destructive validation decision

Real reset-credit redeem is intentionally SKIPPED for v1.5.0 release validation. This is an explicit release-scope decision permitted by TASK-573 because destructive behavior is already covered through protocol fixtures, deterministic mock paths, fault injection, persistent recovery tests, and GUI confirmation validation.

No unresolved P0 criterion remains.
