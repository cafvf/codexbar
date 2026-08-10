# CodexBar v1.5 — Detailed Traceability

Status: frozen planned traceability
Purpose: map every acceptance criterion to implementation task(s) and planned automated evidence.

## REQ-RESET-001

| AC | Tasks | Planned automated evidence |
|---|---|---|
| AC-RESET-001..003 | 511,513,514 | test_account_ports, test_account_rate_limits_parser, test_usage_provider_adapter |
| AC-RESET-004..010 | 510,513 | test_reset_models, test_account_rate_limits_parser |
| AC-RESET-011..015 | 510,513 | test_reset_models, parser fixtures |
| AC-RESET-016 | 513 | future-enum parser fixture |
| AC-RESET-017 | 516 | current-account controller + architecture guard |
| AC-RESET-018 | 513,516 | optional-subtree degradation test |
| AC-RESET-019 | 513,517 | one-read-per-refresh acceptance |
| AC-RESET-020 | 510,513 | model/parser persistence-boundary architecture test |

## REQ-RESET-LEDGER-001

| AC | Tasks | Planned automated evidence |
|---|---|---|
| AC-LEDGER-001..007 | 521,522,523 | reset_event_paths, reset_event_sqlite |
| AC-LEDGER-008..018 | 524,525,527 | reset_projection, reset_event_derivation, reset_deadline_events |
| AC-LEDGER-019 | 524 | unresolved-attempt projection tests |
| AC-LEDGER-020..022 | 526 | reset_ledger_service failure/current-state tests |
| AC-LEDGER-023..024 | 528 | reset_ledger_cli |
| AC-LEDGER-025 | 523 | normalized payload/privacy test |

## REQ-BUDGET-001

| AC | Tasks | Planned automated evidence |
|---|---|---|
| AC-BUDGET-001..006 | 530,534 | usage_reserve_policy, budget_policy |
| AC-BUDGET-007..011 | 531,532,533,537 | settings migration/v2/architecture tests |
| AC-BUDGET-012..015 | 535 | budget_runtime |
| AC-BUDGET-016 | 562 | budget UI acceptance |
| AC-BUDGET-017 | 531,532,536 | existing settings regression + migration tests |

## REQ-RESET-ACTION-001

| AC | Tasks | Planned automated evidence |
|---|---|---|
| AC-REDEEM-001..004 | 541,542,543 | state machine/begin/process-manager tests |
| AC-REDEEM-005..007 | 542,545 | ledger-failure and retry tests |
| AC-REDEEM-008..010 | 540,543 | consumer gateway/process manager |
| AC-REDEEM-011..013 | 543,544 | refetch + unknown-outcome tests |
| AC-REDEEM-014 | 546 | restart recovery |
| AC-REDEEM-015..017 | 547 | account operation ordering + UI later |
| AC-REDEEM-018..020 | 548,564 | fault injection + UI acceptance/privacy checks |

## REQ-RESET-MONITOR-001

| AC | Tasks | Planned automated evidence |
|---|---|---|
| AC-MONITOR-001..003 | 552,553 | situation/policy tests |
| AC-MONITOR-004..009 | 554,555 | expiry monitor/deadline runtime |
| AC-MONITOR-010..017 | 553,558 | policy boundaries/failure isolation |
| AC-MONITOR-018 | 550,551,556 | notification transport + usage regression |
| AC-MONITOR-019 | 552,557 | no-second-poll/no-forecast architecture |

## Cross-invariants

| Invariant | Tasks | Evidence |
|---|---|---|
| INV-V15-001 UsageSnapshot remains reset-free | 511,513 | architecture test |
| INV-V15-002 one normal read | 513,517 | call-count acceptance |
| INV-V15-003 no ledger current fallback | 516,526 | controller/service tests |
| INV-V15-004 authoritative count | 510,513 | parser/model tests |
| INV-V15-005 expiresAt null = non-expiring | 510,513 | model/parser tests |
| INV-V15-006 partial omission not causal | 525 | derivation negative test |
| INV-V15-007 complete omission only removal | 525 | derivation positive test |
| INV-V15-008 not event sourced | 524,526 | architecture/current-source tests |
| INV-V15-009 no auto redeem | 543,557 | architecture test |
| INV-V15-010 durable intent first | 542,543 | ordering spy/fake test |
| INV-V15-011 same uncertain attempt ID | 545 | retry test |
| INV-V15-012 account operations serialized | 515,547 | coordinator ordering tests |
| INV-V15-013 no forecast | 553,557 | policy + architecture |
| INV-V15-014 budget != UsageState | 534 | budget policy |
| INV-V15-015 history schema 1 | 517,574 | schema/regression |
| INV-V15-016 schema1 settings readable | 531 | migration test |
| INV-V15-017 schema2 explicit save | 532 | codec test |
| INV-V15-018 no secrets/raw payload persistence | 523,548 | privacy tests |
| INV-V15-019 reset taxonomy separation | 510,520,552 | type/architecture tests |
| INV-V15-020 v1.4 GUI lifecycle | 566,574 | lifecycle acceptance/manual target |
