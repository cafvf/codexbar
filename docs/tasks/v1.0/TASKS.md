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

## REQ-UI-001 — Linux tray (next vertical slice)
- [ ] TASK-020 specify tray lifecycle, refresh cadence and error presentation.
- [ ] TASK-021 write acceptance tests for tray behavior.
- [ ] TASK-022 implement PySide6 tray shell.
- [ ] TASK-023 move refresh off GUI thread.
- [ ] TASK-024 Linux GUI smoke tests.
- [ ] TASK-025 packaging and desktop autostart.
