# Traceability — REQ-ALERT-001

Status: closed
Release: v1.2

| Requirement area | Acceptance evidence | Primary implementation | Status |
|---|---|---|---|
| Baseline | AC-ALERT-001..004 | `application/alerts.py` | validated |
| Alertable transitions | AC-ALERT-005..009 | `application/alerts.py` | validated |
| Deduplication/re-arm | AC-ALERT-010..014 | `application/alerts.py` | validated |
| Notification settings | AC-ALERT-015..018 | `application/alerts.py`, `ui/controller.py` | validated |
| Stale/error isolation | AC-ALERT-019..021 | `application/alerts.py`, `application/refresh.py`, `ui/controller.py` | validated |
| Event/delivery contract | AC-ALERT-022..025 | `application/alerts.py`, `application/ports.py`, `infrastructure/notifications.py` | validated |
| Physical desktop presentation | AC-ALERT-026 | `infrastructure/notifications.py`, target validation harness | validated |

## Evidence locations

- `tests/acceptance/test_req_alert_001.py`
- `tests/acceptance/test_req_alert_001_coverage.py`
- `tests/acceptance/test_req_alert_001_regressions.py`
- `tests/acceptance/test_architecture_invariants.py`
- `tests/unit/test_alerts.py`
- `tests/unit/test_alert_runtime_controller.py`
- `tests/unit/test_notifications.py`
- `tests/unit/test_alert_validation_harness.py`
- `scripts/validate_alerts.py`
- `scripts/diagnose_notifications.py`
- `docs/VALIDATION-REQ-ALERT-001.md`
- `docs/adr/ADR-006-linux-notifications.md`

## Compatibility conclusions

- settings schema remains v1;
- LOW threshold remains sourced from `AppSettings -> UsagePolicy`;
- no persisted alert state was added;
- notification failures remain outside the usage refresh success/failure contract;
- final Linux transport dependency is `notify-send` / `libnotify-bin`.

REQ-ALERT-001 is fully traceable and closed.
