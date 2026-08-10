# UC-1610 — Context failure isolation

## Scenario
History/context query fails or history database is unreadable.

## Expected behavior
- Current usage remains visible;
- Control/Budget remains functional;
- reset-credit/redeem remains governed by its own state;
- Context shows unavailable/diagnostic state;
- no historical value is fabricated.
