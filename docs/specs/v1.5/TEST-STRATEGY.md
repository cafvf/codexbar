# CodexBar v1.5 Test Strategy

Status: implementation-ready test strategy

## Goal

Protect behavior and architecture without repeating the v1.4 mistake of overfitting acceptance tests to
source-text implementation details.

## Test layers

### Domain/unit

Test:
- reset detail coverage;
- expiry knowledge;
- timestamp normalization;
- reserve/headroom;
- ResetOpportunityPolicy;
- event projection fold;
- redeem state transitions.

Prefer value-based tests.

### Application/contract

Use fake ports to test:
- one composed read produces usage + reset state;
- ledger event derivation/dedup;
- restart projection;
- redeem REQUESTED-before-send invariant;
- uncertain retry reuses attempt ID;
- account-operation serialization;
- settings migration v1->v2;
- notification message formatting.

### Infrastructure

JSON-RPC fixtures:
- count only;
- partial details;
- complete details;
- expiresAt concrete/null;
- duplicate IDs;
- n_details > availableCount;
- unknown future enum strings;
- all consume outcomes;
- timeout after send.

SQLite:
- fresh schema;
- restart;
- corruption;
- unsupported version;
- event ordering;
- atomic append;
- inspect.

Settings:
- schema 1 read/no rewrite;
- schema 2 write/read;
- corrupt/unsupported behavior.

### UI/acceptance

Behavioral tests:
- reset count/detail rendered;
- non-expiring versus unknown expiry text;
- redeem confirmation;
- double click cannot duplicate attempt;
- unresolved attempt recovery UI;
- budget update runtime;
- History lifecycle regression remains green;
- Current card identity remains stable during unchanged polling.

Avoid source-string assertions for Qt signal implementation unless enforcing an actual architecture boundary.

### Architecture tests

Protect:
- UI does not import infrastructure;
- domain does not import application/UI/infrastructure;
- app-server gateway is infrastructure;
- ResetOpportunityPolicy has no infrastructure/UI dependency;
- UsageSnapshot has no reset-credit field/import;
- history schema remains 1;
- reset Event Store uses its own schema/database;
- account reader and reset consumer are separate ports;
- current reset inventory never reads from ledger projection.

## Critical fault-injection scenarios

1. usage valid, reset subtree malformed;
2. reset ledger write failure during ordinary read;
3. reset ledger write failure before redeem;
4. process restart with REQUESTED attempt;
5. timeout/EOF after consume may have been sent;
6. retry returns alreadyRedeemed;
7. consume reset succeeds then refetch fails;
8. concurrent manual refresh requested during redeem;
9. COUNT_ONLY after previously COMPLETE details;
10. PARTIAL omission of known credit;
11. COMPLETE omission of known credit;
12. local clock crosses expiry while app remains running.

## Target validation additions

Manual target validation SHALL include:
- real reset inventory count if account exposes it;
- expiry rendering for a known credit when available;
- redeem flow only when the user intentionally chooses to test a real credit;
- restart after an unresolved-attempt test may use mock/fault-injection rather than risking a real second
  credit;
- History/Refresh lifecycle scenarios from v1.4 remain part of regression validation.
