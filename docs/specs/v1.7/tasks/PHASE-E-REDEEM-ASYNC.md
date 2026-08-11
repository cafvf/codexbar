# Phase E — Asynchronous Redeem

Tasks: TASK-750..759

## Goal

Keep durable redeem semantics while moving external work off Qt.

## Tasks

- TASK-750: implement framework-independent RedeemExecutionController.
- TASK-751: define idle/running/result/error UI execution state.
- TASK-752: submit existing process-manager redeem/retry to worker.
- TASK-753: prevent duplicate start while active.
- TASK-754: suppress late UI adoption after close/obsolete lifecycle.
- TASK-755: preserve account-operation serialization.
- TASK-756: run all v1.5/v1.6 redeem/idempotency/recovery regressions.
- TASK-757: delayed-fake responsiveness characterization.
- TASK-758: physical manual redeem/retry smoke when safe/capability available.
- TASK-759: confirm no automatic redeem path was introduced.

## Gate E

External consume/refetch is off Qt; process-manager semantics unchanged; delayed
fake proves responsiveness; physical PASS or justified capability SKIP; global
gate green.
