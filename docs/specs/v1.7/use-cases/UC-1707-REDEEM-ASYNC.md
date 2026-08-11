# UC-1707 — Redeem a reset credit without freezing UI

## Preconditions
Redeem is available and user confirms.

## Flow
1. UI controller enters running state.
2. Existing RedeemProcessManager executes in a worker.
3. Buttons remain protected against duplicate invocation.
4. Result returns and is adopted on the UI thread.

## Expected
Durable/idempotent semantics are unchanged and Qt stays responsive.
