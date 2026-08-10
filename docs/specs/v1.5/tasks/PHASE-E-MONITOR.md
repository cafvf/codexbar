# Phase E — Reset Monitor and Notification Generalization

Goal: turn reset facts + reserve into deterministic advice without forecasting.

## TASK-550 — Transport-neutral notification message

Generalize NotificationPort away from AlertEvent to NotificationMessage:
- summary;
- body;
- urgency.

Adapt notify-send infrastructure.

Tests:
`tests/unit/test_notification_message.py`.

## TASK-551 — Preserve existing usage alerts

Adapt AlertService to format/send NotificationMessage while keeping LOW/EXHAUSTED transition semantics and
delivery isolation unchanged.

Tests:
existing alert/notification tests + `tests/acceptance/test_v1_5_usage_alert_regression.py`.

## TASK-552 — ResetSituation builder

Build factual situation from current account state, budget policy and unresolved redeem projection.
Do not infer unavailable data.

Tests:
`tests/unit/test_reset_situation.py`.

## TASK-553 — ResetOpportunityPolicy

Implement pure priority policy and constants:
- 24h watch;
- 6h urgent;
- 2h scheduled-reset-near;
- 5pp meaningful headroom.

Test equality boundaries exactly.

Tests:
`tests/unit/test_reset_opportunity_policy.py`.

## TASK-554 — Expiry fact monitor

Detect horizon crossings (24h, 6h, 1h), discovery/count facts as scoped, and deduplicate by credit/horizon.

No expiry event for DOES_NOT_EXPIRE or unknown detail.

Tests:
`tests/unit/test_reset_expiry_monitor.py`.

## TASK-555 — Runtime deadline event recording

While app is running, record CREDIT_EXPIRY_DEADLINE_PASSED once when known deadline crosses.
Reuse Phase B primitive.

Tests:
`tests/unit/test_reset_deadline_runtime.py`.

## TASK-556 — Reset notifications

Map factual reset monitor events and policy advice to distinct NotificationMessage wording/urgency.

Factual and advisory notifications must remain distinguishable.

Tests:
`tests/unit/test_reset_notifications.py`.

## TASK-557 — No-forecast architecture guard

Protect monitor/policy from history analytics, recent slope, agent count or forecast dependencies.

Tests:
`tests/architecture/test_v1_5_no_forecast.py`.

## TASK-558 — Monitor failure isolation

Notification delivery/ledger diagnostic failures do not break Current/redeem process state.

Tests:
`tests/acceptance/test_v1_5_monitor_failures.py`.

## TASK-559 — Phase E regression gate

Run Gate E.
