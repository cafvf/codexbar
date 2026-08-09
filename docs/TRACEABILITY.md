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
| REQ-UI-002 | AC-UI-016..019 | `ui.native_indicator`, `ui.tray` | `test_native_indicator.py`, `test_req_ui_002.py` | validated on target Linux |
| REQ-UI-002 | AC-UI-020..024 | `ui.native_indicator`, `ui.native_indicator_helper`, ADR-003 | `test_native_indicator.py`, architecture tests | validated on target Linux |

| REQ-UI-002 / UC-UI-007 | AC-UI-027..031 | `run_indicator_diagnostics`, helper `--diagnose`, CLI `--diagnose-indicator` | `tests/unit/test_native_indicator.py` | TASK-029E/F | ADR-003 |

| REQ-UI-002 / UC-UI-007 | AC-UI-032..033 | `sanitized_native_environment`, all system-Python launch sites | `tests/unit/test_native_indicator.py` sanitizer/launch regression tests | TASK-029G | ADR-003 |


## REQ-UI-002 supervision, diagnostics and environment isolation

| Requirement | Criteria | Implementation | Tests | Status |
|---|---|---|---|---|
| REQ-UI-002 | AC-UI-025..026 | `ui.native_indicator`, `ui.tray` | native-helper supervision tests | validated |
| REQ-UI-002 | AC-UI-027..031 | indicator diagnostic CLI/helper | diagnostic unit/CLI tests | validated |
| REQ-UI-002 | AC-UI-032..033 | sanitized helper launcher environment | native environment sanitization tests | validated on target VS Code/Snap-contaminated launch path |

Target evidence and limitations are recorded in `docs/VALIDATION.md`.


## REQ-DESKTOP-001 distribution and XDG integration

| Requirement | Criteria | Implementation | Tests | Status |
|---|---|---|---|---|
| REQ-DESKTOP-001 | AC-DESKTOP-001..004 | `desktop.py`, `scripts/install.sh` | `test_req_desktop_001.py` | validated |
| REQ-DESKTOP-001 | AC-DESKTOP-005..006 | `desktop.py` autostart operations | acceptance/unit tests | validated |
| REQ-DESKTOP-001 | AC-DESKTOP-007..010 | status/uninstall managed ownership checks | acceptance/unit tests | validated |
| REQ-DESKTOP-001 | AC-DESKTOP-011..013 | `scripts/install.sh`, `scripts/uninstall.sh`, uv-tool launcher | script/acceptance checks + target validation | validated |

## REQ-DESKTOP-001 host-user isolation

| Requirement | Criteria | Implementation | Tests | Status |
|---|---|---|---|---|
| REQ-DESKTOP-001 | AC-DESKTOP-014 | `desktop._xdg_data_home`, `desktop._xdg_config_home` | desktop acceptance/unit Snap-XDG regression tests | validated |
| REQ-DESKTOP-001 | AC-DESKTOP-015 | `scripts/install.sh`, `scripts/uninstall.sh` | installer policy unit test | validated |
| REQ-DESKTOP-001 | AC-DESKTOP-016 | `scripts/install.sh` legacy-install notice | installer policy review + target observation | validated |
## v1.1 — REQ-SETTINGS-001

The detailed settings traceability matrix is maintained in
`docs/TRACEABILITY-REQ-SETTINGS-001.md`.

| Requirement | Criteria | Primary implementation | Primary evidence | Status |
|---|---|---|---|---|
| REQ-SETTINGS-001 | AC-SETTINGS-001..011 | `domain/settings.py`, `application/settings.py`, `infrastructure/settings.py` | settings acceptance/unit tests | validated |
| REQ-SETTINGS-001 | AC-SETTINGS-012..014 | `UsagePolicy`, `ui/controller.py`, runtime timer integration | controller/runtime tests + target validation | validated |
| REQ-SETTINGS-001 | AC-SETTINGS-015..019 | shared reset/get use cases and CLI | acceptance/CLI tests | validated |
| REQ-SETTINGS-001 | AC-SETTINGS-020..024 | `ui/settings.py`, Qt tray, Ayatana Settings intent | GUI tests + Ubuntu/GNOME/Wayland validation | validated |

ADR-005 records the schema-v1 persistence compatibility boundary. The v1.1 release scope is closed.
