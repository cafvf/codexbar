# REQ-UI-001 — Linux tray presentation and refresh

Status: implemented / target-desktop regression validation pending  
Priority: P0  
Release: v1.0

## Requirement
CodexBar SHALL expose the current normalized usage state through a Linux system-tray interface without
blocking the GUI thread, while preserving explicit freshness and error semantics from REQ-USAGE-001.

## Scope decisions
- The tray UI is optional at installation time; the headless core remains usable without PySide6.
- Automatic refresh defaults to 60 seconds and is an explicit `TraySettings` policy.
- Refresh work executes outside the GUI thread. Qt only polls completion and renders immutable state.
- v1.0 tray scope includes display, manual/automatic refresh, stale/error states, and clean shutdown.
- System-tray activation semantics are desktop-dependent. The application SHALL provide a useful and
  escapable interaction even when the desktop does not emit Qt `Trigger`/`Context` activation reasons.
- Desktop autostart/packaging integration is a separate completion task because it depends on the target
  Linux desktop environment.

### UC-UI-001 — Start and refresh the tray
On startup the tray SHALL immediately request usage data and SHALL periodically request another snapshot.

- AC-UI-001: starting a refresh returns control immediately and exposes `LOADING`; provider work is
  delegated to an executor rather than performed by the GUI caller.
- AC-UI-002: a successful refresh maps the snapshot to `FRESH` immutable presentation state.
- AC-UI-005: if a refresh is already running, another refresh request is rejected rather than spawning
  overlapping provider calls.

### UC-UI-002 — Preserve useful information through failure
The tray SHALL distinguish stale cached data from an initial hard failure.

- AC-UI-003: after at least one valid snapshot, a transient provider failure renders the prior snapshot as
  `STALE` and does not fabricate new values.
- AC-UI-004: if the first refresh fails and no cached snapshot exists, the tray renders `ERROR` with no
  fabricated usage state.

### UC-UI-003 — Present usage in the desktop shell
The tray shell SHALL provide a compact panel containing every usage window reported by the view model,
remaining percent, reset time when available, observation time, and refresh status.

- AC-UI-006A: on desktops that emit `Trigger`, primary activation toggles the compact panel.
- AC-UI-006B: `DoubleClick` also toggles the compact panel as a compatibility path.
- AC-UI-006C: a registered context menu SHALL remain available as the portable tray control surface; its
  first line SHALL expose current glance usage directly, without requiring a `Show` action merely to read
  the quotas.
- AC-UI-007: the tray menu SHALL provide Refresh, Open details, and Quit actions.
- AC-UI-007A: the compact details panel SHALL also provide a Quit action so the user retains an explicit
  shutdown path even when tray-menu activation is constrained by the desktop shell.
- AC-UI-008: refresh timers and result polling do not execute the provider call on the Qt GUI thread.

## Portability rationale
Qt documents `Trigger`, `Context`, `DoubleClick`, and other activation reasons, but its Qt-for-Python
system-tray documentation also notes that, on GNOME Shell since 3.26, not all activation reasons are
supported without shell extensions. Consequently, v1.0 treats direct primary activation as a capability,
not as a universal Linux invariant. The invariant is that one activation exposes useful usage information
and that a reliable Quit path is always reachable.

## Validation gate
REQ-UI-001 is not considered fully validated until its PySide6 smoke test and a manual tray interaction
pass on the target Linux desktop with the authenticated Codex provider. Two target observations refined
this gate: the registered menu initially consumed primary click, while removing the registered menu made
single click inert and removed the reliable Quit surface. The adaptive registered-menu design above must
now be revalidated.
