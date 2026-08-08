# Traceability Matrix

| Requirement | Use case | Acceptance criterion | Primary test | Implementation |
|---|---|---|---|---|
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-001 | `tests/acceptance/test_req_usage_001.py::test_ac_usage_001_*` | `infrastructure/app_server.py`, `domain/models.py` |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-002 | `test_ac_usage_002_*` | `parse_rate_limits_response` |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-003 | `test_ac_usage_003_*` | `parse_rate_limits_response` |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-004 | `test_ac_usage_004_*` | `Fraction` |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-005 | `test_ac_usage_005_*` | `_parse_window` |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-006 | `test_ac_usage_006_*` | `domain/errors.py`, provider |
| REQ-USAGE-001 | UC-USAGE-001 | AC-USAGE-007 | `test_ac_usage_007_*` | parser validation |
| REQ-USAGE-001 | UC-USAGE-002 | AC-USAGE-008 | `test_ac_usage_008_*` | `UsageWindow.state`, ViewModel |
| REQ-USAGE-001 | UC-USAGE-002 | AC-USAGE-009 | `test_architecture_invariants.py` | package boundaries |
| REQ-USAGE-001 | UC-USAGE-003 | AC-USAGE-010 | `test_ac_usage_010_*` | `RefreshCoordinator` |
