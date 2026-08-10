# Phase D — Redeem Process Manager

Goal: implement the dangerous side effect only after durable ledger/idempotency infrastructure is green.

## TASK-540 — Consume RPC in app-server Gateway

Implement `account/rateLimitResetCredit/consume` behind ResetCreditConsumer.

Map the four documented outcomes.
Keep opaque credit ID optional.

Tests:
`tests/unit/test_reset_consumer_gateway.py`.

## TASK-541 — Redeem process state machine

Implement attempt identity/status derived from ledger events:
REQUESTED, OUTCOME_UNKNOWN and terminal outcomes.

`RedeemAttemptId == idempotencyKey`.

Tests:
`tests/unit/test_redeem_state_machine.py`.

## TASK-542 — Durable begin-attempt use case

Create new logical attempt only after explicit application command and persist REDEEM_REQUESTED before
returning permission to send.

Ledger failure -> fail closed.

Tests:
`tests/unit/test_redeem_begin.py`.

## TASK-543 — Redeem Process Manager

Orchestrate:
- durable begin;
- serialized consume;
- outcome append;
- authoritative composed refetch for success/idempotent success.

No UI yet.

Tests:
`tests/unit/test_redeem_process_manager.py`.

## TASK-544 — Unknown-outcome handling

Model transport/process ambiguity when the request may have been sent.

Persist OUTCOME_UNKNOWN without inventing success/failure.

Tests:
`tests/unit/test_redeem_unknown_outcome.py`.

## TASK-545 — Same-attempt retry

Retry unresolved attempt using exactly the same attempt/idempotency ID.
Do not require a new logical confirmation as though it were a different redemption; UI recovery confirmation
may still be required before sending.

Tests:
`tests/unit/test_redeem_retry.py`.

## TASK-546 — Restart recovery

Projection exposes unresolved attempts after restart.
Application exposes recovery command/state and never silently replaces one with a new attempt.

Tests:
`tests/unit/test_redeem_restart_recovery.py`.

## TASK-547 — Account-operation ordering

Prove:
- refresh cannot publish stale pre-redeem state after post-redeem refetch;
- duplicate/concurrent redeems are serialized/rejected;
- normal auto-refresh waits safely.

Tests:
`tests/unit/test_account_operation_ordering.py`.

## TASK-548 — Fault-injection matrix

Automate:
- ledger failure before consume;
- timeout after possible send;
- `alreadyRedeemed` retry;
- success followed by refetch failure;
- app-server process exit.

Tests:
`tests/acceptance/test_v1_5_redeem_faults.py`.

## TASK-549 — Phase D regression gate

Run Gate D.
Only after PASS may production redeem UI be introduced.
