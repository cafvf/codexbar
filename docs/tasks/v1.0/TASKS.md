# v1.0 Tasks

## REQ-USAGE-001 — Core
- [x] TASK-001 `Fraction` value object — AC-001, AC-004.
- [x] TASK-002 dynamic `UsageWindow` model — AC-002, AC-003, AC-005, AC-008.
- [x] TASK-003 `UsageSnapshot`, uniqueness and freshness — AC-002, AC-010.
- [x] TASK-004 normalized error taxonomy — AC-006, AC-007.
- [x] TASK-005 `UsageProvider` port — UC-001.
- [x] TASK-006 `GetCurrentUsage` — UC-001.
- [x] TASK-007 canonical captured/sanitized app-server fixtures.
- [x] TASK-008 verify production source and accept ADR-002.
- [x] TASK-009 implement `CodexAppServerProvider` and parser — AC-001..007.
- [x] TASK-010 explicit LOW-state policy instead of hidden threshold.
- [x] TASK-011 `UsageViewState` / mapper — AC-008.
- [x] TASK-012 architecture dependency tests — AC-009.
- [x] TASK-013 stale refresh coordinator — AC-010.
- [x] TASK-014 CLI smoke surface for real provider and `--mock` diagnostics.
- [x] TASK-015 validate authenticated real provider on target Linux workstation.

## REQ-UI-001 — Linux tray
- [x] TASK-020 specify tray lifecycle, cadence, stale/error presentation and validation gate.
- [x] TASK-021 write acceptance tests for asynchronous tray behavior.
- [x] TASK-022 implement optional PySide6 tray shell and compact usage panel.
- [x] TASK-023 move provider refresh off the GUI thread and prevent overlapping refreshes.
- [x] TASK-024 add optional Qt smoke test harness.
- [x] TASK-025 perform first target Qt tray validation; icon/panel/quit worked but AC-UI-006 failed because primary click opened the context menu.
- [x] TASK-026 remove the registered tray context menu and route `Trigger` to panel toggle / `Context` to a manually popped menu.
- [x] TASK-027 revalidate corrected primary-click behavior on target Linux; result: `Trigger` remained unavailable and removing the registered menu removed the reliable Quit path.
- [x] TASK-027A implement adaptive tray interaction: registered live-data menu, `Trigger`/`DoubleClick` detail toggle, and panel-level Quit.
- [x] TASK-027B revalidate adaptive tray interaction and shutdown paths on target Linux.

## REQ-UI-002 — Tray identity and glanceable usage
- [x] TASK-028 specify project-owned tray identity and canonical glance string.
- [x] TASK-029 implement compact window labels (`5h`, `W`) and tooltip fallback.
- [x] TASK-029A replace generic computer icon with project-owned terminal-style icon.
- [x] TASK-029B validate project icon plus dynamic glance tooltip/menu summary on target Linux.
- [x] TASK-029C evaluate and implement an optional Ayatana native Linux indicator backend for adjacent dynamic text; preserve Qt fallback.
- [x] TASK-029C1 record target failure of PyGObject-from-PyPI and adopt ADR-003 system-Python helper boundary.
- [x] TASK-029C2 remove PyGObject from uv dependencies and implement JSONL native helper + capability probe.
- [x] TASK-029D validate system-Python helper selection and physical adjacent-label rendering on target Linux.
- [x] TASK-029E diagnose Snap/IDE runtime contamination and add native-helper environment sanitization.
- [x] TASK-029F revalidate native Ayatana indicator from the previously contaminated VS Code environment.

## REQ-DESKTOP-001 — v1.0 completion
- [x] TASK-030 specify supported user-local uv-tool/XDG installation strategy — REQ-DESKTOP-001.
- [x] TASK-031 implement desktop entry, project icon, status and install workflow — AC-DESKTOP-001..004,007,011,013.
- [x] TASK-032 implement opt-in autostart and managed removal path — AC-DESKTOP-005..006,008..010,012.
- [x] TASK-033 validate clean install, desktop launch, checkout independence, autostart and uninstall on target Linux.

### Release-hardening and target-regression tasks
- [x] TASK-040 require bounded `ready` handshake before accepting the Ayatana helper.
- [x] TASK-041 monitor helper liveness and activate Qt fallback on unexpected exit.
- [x] TASK-042 add provider-independent native-indicator diagnostics — AC-UI-027..031.
- [x] TASK-043 diagnose Snap/VS Code native-runtime contamination on the target workstation.
- [x] TASK-044 sanitize all system-Python native-indicator launches — AC-UI-032..033.
- [x] TASK-045 revalidate native indicator visibility from the VS Code integrated terminal.
- [x] TASK-046 correct repository-wide ruff violations exposed by the target release-gate run.
- [x] TASK-047 package `py.typed` and configure strict mypy source checking.
- [x] TASK-048 rerun pytest/ruff/mypy/compileall gates during release hardening.
- [x] TASK-049 reproduce and specify Snap-scoped XDG/uv installation contamination.
- [x] TASK-050 pin canonical host-user uv/XDG locations in install/uninstall scripts.
- [x] TASK-051 reject `$HOME/snap/` XDG homes and add regression tests.
- [x] TASK-052 revalidate canonical installation from the VS Code/Snap terminal.
- [x] TASK-053 remove the legacy sandbox-scoped uv tool after canonical-install validation.
- [x] TASK-054 complete uninstall/reinstall acceptance cycle and close REQ-DESKTOP-001.
- [x] TASK-055 align package/release metadata to version 1.0.0 and prepare release tag.
