# CodexBar v1.5 — Planned Test Matrix

Status: frozen planned matrix

## New automated test groups

### Unit / pure
- `test_reset_models.py`
- `test_account_ports.py`
- `test_account_rate_limits_parser.py`
- `test_usage_provider_adapter.py`
- `test_account_operation_coordinator.py`
- `test_current_account_controller.py`
- `test_reset_events.py`
- `test_reset_projection.py`
- `test_reset_event_derivation.py`
- `test_reset_deadline_events.py`
- `test_usage_reserve_policy.py`
- `test_settings_schema_v1_migration.py`
- `test_settings_schema_v2.py`
- `test_budget_policy.py`
- `test_redeem_state_machine.py`
- `test_redeem_process_manager.py`
- `test_redeem_unknown_outcome.py`
- `test_redeem_retry.py`
- `test_reset_situation.py`
- `test_reset_opportunity_policy.py`
- `test_reset_expiry_monitor.py`
- `test_reset_notifications.py`

### Infrastructure
- `test_app_server_gateway.py`
- `test_reset_event_paths.py`
- `test_reset_event_sqlite.py`
- `test_reset_consumer_gateway.py`

### Architecture
- `test_v1_5_account_boundaries.py`
- `test_v1_5_composition_root.py`
- `test_v1_5_settings_architecture.py`
- `test_v1_5_no_forecast.py`

### Acceptance
- `test_reset_ledger_cli.py`
- `test_v1_5_redeem_faults.py`
- `test_v1_5_usage_alert_regression.py`
- `test_v1_5_monitor_failures.py`
- `test_req_reset_ui_001.py`
- `test_req_budget_ui_001.py`
- `test_req_budget_settings_ui_001.py`
- `test_req_redeem_ui_001.py`
- `test_req_redeem_recovery_ui_001.py`
- `test_v1_5_gui_lifecycle_regressions.py`
- `test_v1_5_tray_regression.py`

## Mandatory regression families

Existing tests for:
- app-server usage parsing;
- refresh STALE fallback;
- usage history capture/query/analytics;
- settings schema-1 behavior;
- usage alert transitions;
- Current Details rendering;
- History UI and lifecycle;
- native indicator;
- CLI;
- architecture/import boundaries.

shall remain in the full gate.

## Boundary-value matrix

Reset detail:
- count 0/details [];
- count >0/details null;
- n<count;
- n=count;
- n>count;
- duplicate IDs;
- grantedAt min/invalid;
- expiresAt past/future/null/invalid.

Budget:
- reserve 0;
- reserve 1;
- remaining below/equal/above reserve;
- 5pp headroom exactly.

Monitor:
- expiry exactly 24h;
- just below/above 24h;
- exactly 6h;
- exactly 2h scheduled reset;
- exactly 5pp headroom;
- unresolved redeem priority.

Redeem:
- reset;
- alreadyRedeemed;
- nothingToReset;
- noCredit;
- transport error before definite send when distinguishable;
- possible-send timeout/EOF;
- refetch success/failure.
