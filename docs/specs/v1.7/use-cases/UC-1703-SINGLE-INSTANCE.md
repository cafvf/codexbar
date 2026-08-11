# UC-1703 — Launch CodexBar when it is already running

## Preconditions
One healthy GUI owner is listening on its local IPC endpoint.

## Flow
1. User launches `codexbar --gui` again.
2. New process connects to owner.
3. It sends `PING`, then `SHOW_DETAILS`.
4. Existing owner shows/focuses Open Details.
5. New process exits.

## Expected
Only one polling/notification/redeem-capable runtime remains.
