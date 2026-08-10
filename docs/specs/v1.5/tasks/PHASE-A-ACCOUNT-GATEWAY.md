# Phase A — Composed Account Gateway

Goal: introduce the final v1.5 read architecture without changing user-visible behavior beyond making
normalized reset current state available to later phases.

## TASK-510 — Reset current-domain value types

Implement pure normalized types required by REQ-RESET-001:
- `ResetCreditId` or equivalent opaque validated identity;
- detail coverage;
- expiry knowledge;
- ResetCreditDetail;
- ResetCreditInventory;
- ResetCreditReadResult.

Constraints:
- mandatory granted_at for detailed rows;
- EXPIRES_AT vs DOES_NOT_EXPIRE distinction;
- no infrastructure imports.

Tests:
`tests/unit/test_reset_models.py`

Covers:
AC-RESET-004..015, AC-RESET-020.

## TASK-511 — Application account-read contracts

Add:
- `AccountRateLimitsObservation`;
- `AccountRateLimitsReader` port;
- `ResetCreditConsumer` port contract placeholder;
- compatibility relation to existing UsageProvider.

Do not implement consume behavior yet.

Tests:
`tests/unit/test_account_ports.py`
`tests/architecture/test_v1_5_account_boundaries.py`

Covers:
AC-RESET-001..003.

## TASK-512 — Extract Codex app-server Gateway

Refactor app-server infrastructure so handshake/JSON-RPC request mechanics are reusable by:
- composed account read;
- later consume.

No intended usage behavior change.

Preserve current error taxonomy and stdio transport semantics.

Tests:
existing app-server tests + `tests/unit/test_app_server_gateway.py`.

## TASK-513 — Parse composed account response

Parse the same `account/rateLimits/read` response into:
- existing canonical UsageSnapshot;
- normalized reset read result.

Reset-subtree degradation SHALL be isolatable from valid usage where possible.

Add fixtures:
- reset capability null;
- count-only;
- partial;
- complete;
- duplicate IDs;
- details > count;
- expiresAt concrete/null;
- future/unknown enum strings.

Tests:
`tests/unit/test_account_rate_limits_parser.py`.

## TASK-514 — UsageProvider compatibility adapter

Keep existing one-shot CLI/use cases/tests functional through a UsageProvider projection over the account
reader.

Prove no extra network read is introduced by the adapter path.

Tests:
`tests/unit/test_usage_provider_adapter.py`.

## TASK-515 — Single account-operation lane

Introduce the application-level serialization primitive/coordinator used by refresh now and redeem later.

Requirements:
- one operation at a time;
- safe shutdown;
- no GUI framework dependency;
- read operations preserve existing async behavior.

Tests:
`tests/unit/test_account_operation_coordinator.py`.

## TASK-516 — Composed refresh result

Extend the GUI/application refresh boundary above TrayViewState as needed so one completed account read can
publish usage plus reset-current state without adding reset data to UsageSnapshot.

Keep UsageViewState compatibility and render-on-transition.

Tests:
`tests/unit/test_current_account_controller.py`.

## TASK-517 — Preserve usage history capture

Adapt runtime capture so the composed read:
- records CURRENT usage exactly once;
- keeps STALE exclusion;
- does not perform a second app-server read;
- remains failure-isolated.

Existing HistoryCapturingUsageProvider may remain for legacy/CLI compatibility.

Tests:
`tests/unit/test_v1_5_history_capture_integration.py`.

## TASK-518 — Composition-root migration

Introduce `codexbar/composition.py` or equivalent runtime builder.

Move growing GUI wiring out of `__main__.py` while keeping CLI dispatch and headless imports safe.

Tests:
`tests/architecture/test_v1_5_composition_root.py`.

## TASK-519 — Phase A regression gate

Run Gate A and freeze public account-read interfaces before Phase B.
No functional reset UI yet.
