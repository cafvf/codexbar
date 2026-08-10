# Phase F — GUI Integration

Goal: surface Control while preserving the v1.4 lifecycle architecture.

## TASK-560 — CurrentAccountViewState

Define presentation state combining:
- existing usage view state;
- reset current view state;
- budget/control state;
- redeem recovery/action availability.

Presentation layer must not read repositories directly.

Tests:
`tests/unit/test_current_account_viewmodel.py`.

## TASK-561 — ResetCreditsPanel

Add stable composed widget for:
- authoritative available count;
- count-only/partial/complete coverage;
- known expiry;
- explicitly non-expiring detail;
- data-unavailable state.

Do not add fields to RichUsagePanel.

Tests:
`tests/acceptance/test_req_reset_ui_001.py`.

## TASK-562 — Control/BudgetPanel

Render reserve, usable headroom and deterministic opportunity classification separately from UsageState.

Tests:
`tests/acceptance/test_req_budget_ui_001.py`.

## TASK-563 — Reserve settings UI

Extend Settings dialog for per-window reserve editing.
Save through canonical AppSettings v2 path and apply at runtime.

Tests:
`tests/acceptance/test_req_budget_settings_ui_001.py`.

## TASK-564 — Redeem confirmation UI

Add explicit action only when Phase D process is available.

Known credit:
- show identity-relevant title/expiry if present.

Generic count-only:
- explicitly state backend chooses the credit.

Disable/reject repeated activation while process is active.

Tests:
`tests/acceptance/test_req_redeem_ui_001.py`.

## TASK-565 — Redeem recovery UI

Surface REQUESTED/OUTCOME_UNKNOWN after restart and allow explicit safe retry using same attempt ID.

Do not silently create a new attempt.

Tests:
`tests/acceptance/test_req_redeem_recovery_ui_001.py`.

## TASK-566 — Shell/controller integration

Integrate reset/control panels into Current Details through explicit composition.

Preserve:
- render only on state transition;
- stable widget identity during unchanged polls;
- History top-level lifecycle;
- refresh behavior with History open/hidden.

Tests:
`tests/acceptance/test_v1_5_gui_lifecycle_regressions.py`.

## TASK-567 — Mock reset-credit capability

Extend mock/demo path with deterministic reset inventory and safe simulated consume outcomes for UI/target
validation without spending real credits.

Tests:
`tests/unit/test_mock_reset_credits.py`.

## TASK-568 — Native/Qt integration regression

Ensure native indicator/Qt fallback remain functional.
No reset-credit detail needs to be added to tray text unless explicitly justified by UI design.

Tests:
existing native indicator acceptance + `tests/acceptance/test_v1_5_tray_regression.py`.

## TASK-569 — Phase F regression gate

Run Gate F.
