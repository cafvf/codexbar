# REQ-UI-LIFECYCLE-001 — GUI composition and lifecycle stability

Status: validated — v1.4.0 release candidate
Priority: P0
Release: v1.4
Change taxonomy: HARDENING / INTEGRATION

## Requirement

CodexBar SHALL compose Current Details, History, Settings, native indicator and Qt fallback with explicit
ownership and state-transition boundaries. Periodic polling SHALL detect asynchronous completion without
causing unconditional reconstruction of GUI widgets.

## Acceptance criteria

- `AC-LIFECYCLE-001`: `TrayShell` accepts the already-selected current panel instead of constructing and
  later replacing a legacy panel.
- `AC-LIFECYCLE-002`: unchanged `TrayViewState` does not invoke another current-panel render.
- `AC-LIFECYCLE-003`: widget identity for current cards remains stable between unchanged poll ticks.
- `AC-LIFECYCLE-004`: unexpected worker exceptions are contained at the GUI timer boundary and do not
  call `QApplication.quit`.
- `AC-LIFECYCLE-005`: only a FRESH transition after LOADING may trigger an automatic visible-History reload.
- `AC-LIFECYCLE-006`: History is a sibling/top-level surface, not owned by Current Details.
- `AC-LIFECYCLE-007`: History polling stops while the dialog is hidden and resumes when shown.
- `AC-LIFECYCLE-008`: Settings remains single-instance while open.
- `AC-LIFECYCLE-009`: focused historical identity never falls back silently to another identity.
- `AC-LIFECYCLE-010`: superseded queued history work is cancelled when possible; stale completion remains
  unable to replace a newer request.

## Protected invariants

This requirement SHALL NOT change `Fraction`, `UsageWindowId`, `Freshness`, `UsagePolicy`, SQLite schema 1,
history retention, CURRENT-only history capture, alert classification, settings schema, analytical
semantics or whole-percent CURRENT presentation.
