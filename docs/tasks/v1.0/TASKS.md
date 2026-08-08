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
- [ ] TASK-030 specify supported installation/desktop integration strategy.
- [ ] TASK-031 package launcher/desktop entry without development dependencies.
- [ ] TASK-032 add opt-in autostart support and removal path.
- [ ] TASK-033 validate clean install, startup, shutdown and uninstall on target Linux.


### Native indicator supervision correction
- TASK-UI-017 — require bounded `ready` handshake before accepting the Ayatana helper. [implemented]
- TASK-UI-018 — monitor helper liveness and activate Qt fallback on unexpected exit. [implemented]
- TASK-UI-019 — revalidate native indicator visibility/fallback on target Linux desktop. [pending target validation]
- [x] TASK-029E add provider-independent native-indicator diagnostics with structured step reporting — AC-UI-027..031.
- [x] TASK-029F run `--diagnose-indicator` on the target workstation; isolated failure to Snap/VS Code runtime contamination and confirmed success from a normal system terminal.

- [x] TASK-029G sanitize the environment for all system-Python native indicator launches and add Snap-runtime regression tests — AC-UI-032..033.
- [ ] TASK-029H revalidate native indicator visibility and adjacent label from both VS Code integrated terminal and normal system terminal after sanitization.
