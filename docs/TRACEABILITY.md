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
| REQ-USAGE-001 | UC-USAGE-002 | AC-USAGE-008 | `test_ac_usage_008_*` | `UsageWindow.state`, `UsageViewModel` |
| REQ-USAGE-001 | UC-USAGE-002 | AC-USAGE-009 | `test_architecture_invariants.py` | package boundaries |
| REQ-USAGE-001 | UC-USAGE-003 | AC-USAGE-010 | `test_ac_usage_010_*` | `RefreshCoordinator` |
| REQ-UI-001 | UC-UI-001 | AC-UI-001 | `test_req_ui_001.py::test_ac_ui_001_*` | `ui/controller.py` |
| REQ-UI-001 | UC-UI-001 | AC-UI-002 | `test_req_ui_001.py::test_ac_ui_002_*` | `TrayController`, `UsageViewModel` |
| REQ-UI-001 | UC-UI-002 | AC-UI-003 | `test_req_ui_001.py::test_ac_ui_003_*` | `RefreshCoordinator`, `TrayController` |
| REQ-UI-001 | UC-UI-002 | AC-UI-004 | `test_req_ui_001.py::test_ac_ui_004_*` | `TrayController` |
| REQ-UI-001 | UC-UI-001 | AC-UI-005 | `test_req_ui_001.py::test_ac_ui_005_*` | `TrayController` |
| REQ-UI-001 | UC-UI-003 | AC-UI-006..008 | `tests/gui/test_tray_smoke.py` + target manual smoke | `ui/tray.py`, `ui/launcher.py` |
| REQ-UI-002 | UC-UI-004 | AC-UI-009 | `tests/gui/test_tray_smoke.py::test_ac_ui_009_*` | `ui/tray.py::create_codexbar_icon` |
| REQ-UI-002 | UC-UI-005 | AC-UI-010..013 | `tests/acceptance/test_req_ui_002.py` | `ui/viewmodel.py` |
| REQ-UI-002 | UC-UI-005 | AC-UI-014 | target manual smoke + tooltip formatter tests | `ui/tray.py::_tooltip` |

## REQ-UI-002 native indicator extension

| Requirement | Use case / criteria | Implementation | Tests | Status |
|---|---|---|---|---|
| REQ-UI-002 | AC-UI-009..015 | `ui.viewmodel`, Qt tray | `test_req_ui_002.py`, GUI smoke | target Qt path validated |
| REQ-UI-002 | AC-UI-016..019 | `ui.native_indicator`, `ui.tray` | `test_native_indicator.py`, `test_req_ui_002.py` | implemented; physical label validation pending |
| REQ-UI-002 | AC-UI-020..024 | `ui.native_indicator`, `ui.native_indicator_helper`, ADR-003 | `test_native_indicator.py`, architecture tests | implemented; target helper validation pending |

| REQ-UI-002 / UC-UI-007 | AC-UI-027..031 | `run_indicator_diagnostics`, helper `--diagnose`, CLI `--diagnose-indicator` | `tests/unit/test_native_indicator.py` | TASK-029E/F | ADR-003 |

| REQ-UI-002 / UC-UI-007 | AC-UI-032..033 | `sanitized_native_environment`, all system-Python launch sites | `tests/unit/test_native_indicator.py` sanitizer/launch regression tests | TASK-029G | ADR-003 |


## REQ-UI-002 supervision, diagnostics and environment isolation

| Requirement | Criteria | Implementation | Tests | Status |
|---|---|---|---|---|
| REQ-UI-002 | AC-UI-025..026 | `ui.native_indicator`, `ui.tray` | native-helper supervision tests | validated |
| REQ-UI-002 | AC-UI-027..031 | indicator diagnostic CLI/helper | diagnostic unit/CLI tests | validated |
| REQ-UI-002 | AC-UI-032..033 | sanitized helper launcher environment | native environment sanitization tests | validated on target VS Code/Snap-contaminated launch path |

Target evidence and limitations are recorded in `docs/VALIDATION.md`.
