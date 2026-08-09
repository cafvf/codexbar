# REQ-ALERT-001 — Transition-based desktop usage alerts

Status: specified
Priority: P0
Release: v1.2
Change taxonomy: EVOLUTION

## Requirement

CodexBar SHALL notify the user when a current, successfully refreshed usage window crosses into a
user-relevant constrained state, while suppressing repeated notifications for unchanged state.

The alert system SHALL reuse the existing `UsageWindowState` and configured `UsagePolicy`, SHALL respect the
v1.1 `notifications_enabled` setting, and SHALL treat notification delivery as a failure-isolated external
boundary.

## Definitions

### Alertable states

The initial alertable states are:

- `LOW`;
- `EXHAUSTED`.

`AVAILABLE` is not itself alertable.

### Baseline

The first eligible current snapshot observed after application startup establishes the runtime comparison
baseline. Establishing a baseline SHALL NOT emit an alert, even if a window is already LOW or EXHAUSTED.

This avoids presenting pre-existing state as a newly observed transition.

### Transition

For a stable `UsageWindowId`, an alertable transition occurs when the previous eligible state and current
eligible state differ and the current state is alertable.

Examples:

- `AVAILABLE -> LOW`: alert LOW;
- `AVAILABLE -> EXHAUSTED`: alert EXHAUSTED;
- `LOW -> EXHAUSTED`: alert EXHAUSTED;
- `EXHAUSTED -> LOW`: alert LOW;
- `LOW -> AVAILABLE`: no alert, but re-arms a later LOW/EXHAUSTED transition;
- `EXHAUSTED -> AVAILABLE`: no alert, but re-arms;
- `LOW -> LOW`: no alert;
- `EXHAUSTED -> EXHAUSTED`: no alert.

The policy is state-transition based rather than time/cooldown based.

### Eligible snapshot

Only a successfully obtained `Freshness.CURRENT` snapshot is eligible to establish or advance alert state.

A stale cached snapshot, refresh error, or absence of a new snapshot SHALL NOT establish, advance, reset, or
re-arm alert state.

## Scope decisions

- v1.1 `notifications_enabled` is the only alert enable/disable setting.
- LOW uses `AppSettings.low_remaining_threshold` through the existing `UsagePolicy`.
- EXHAUSTED remains exactly `remaining == 0` under existing domain semantics.
- Each usage window is tracked independently by stable `UsageWindowId`.
- A single current snapshot may generate multiple alert events when multiple windows transition.
- Events are evaluated in the order the windows appear in the normalized snapshot.
- Deduplication state is process-local and is intentionally not persisted.
- Restart establishes a new silent baseline; it does not replay prior transitions.
- A newly appearing window establishes its own silent baseline state.
- A temporarily absent window retains its last eligible state for the lifetime of the process; absence alone
  is not treated as recovery.
- Disabling notifications suppresses delivery but does not freeze transition tracking.
- Re-enabling notifications does not replay transitions that occurred while notifications were disabled.
- Settings schema v1 remains unchanged.
- Alert delivery content is derived from normalized state only; raw Codex payloads/account identifiers are
  outside the alert boundary.

## Alert event contract

Framework-independent alert logic SHALL produce an application-level event containing at least:

- stable window id;
- human-readable window label;
- current `UsageWindowState`;
- current remaining fraction;
- reset timestamp when supplied by the normalized window.

The event SHALL not contain raw provider payloads, credentials, or UI-framework objects.

The presentation adapter may turn this event into a platform notification title/body.

## Architecture

The intended dependency direction is:

`UsageSnapshot + UsagePolicy -> alert transition evaluator -> AlertEvent -> NotificationPort -> desktop adapter`

The transition evaluator belongs outside the UI framework and SHALL be deterministic for a sequence of
eligible snapshots.

The desktop notification mechanism is a volatile external boundary and SHALL be isolated behind a narrow
port. Qt, D-Bus, GI/Ayatana, subprocess, or other platform-specific mechanisms SHALL NOT become domain
dependencies.

The existing `UsageWindow.state(policy)` remains the only classification rule.

No generic event bus, plugin bus, or framework-level dependency-injection container is introduced.

## Failure policy

Expected notification-delivery failures SHALL be normalized or contained at the notification boundary.

A delivery failure SHALL NOT:

- convert a valid usage snapshot into an application refresh error;
- discard the last valid usage display;
- stop future refresh scheduling;
- terminate the tray process;
- mutate usage-window state.

Failed notification delivery is not automatically retried in v1.2. A retry policy would introduce timing and
duplicate-delivery semantics and therefore requires a future requirement.

## Use cases and acceptance criteria

### UC-ALERT-001 — Establish alert baseline

- AC-ALERT-001: the first eligible current snapshot establishes per-window state and emits no alert when all
  windows are AVAILABLE.
- AC-ALERT-002: the first eligible current snapshot emits no alert when one or more windows are already LOW
  or EXHAUSTED.
- AC-ALERT-003: a newly appearing window establishes its own state without alerting merely because its first
  observed state is LOW or EXHAUSTED.
- AC-ALERT-004: a stale snapshot or refresh error cannot establish the initial alert baseline.

### UC-ALERT-002 — Notify on constrained-state transitions

- AC-ALERT-005: `AVAILABLE -> LOW` produces exactly one LOW alert event for that window.
- AC-ALERT-006: `AVAILABLE -> EXHAUSTED` produces exactly one EXHAUSTED alert event for that window.
- AC-ALERT-007: `LOW -> EXHAUSTED` produces exactly one EXHAUSTED alert event.
- AC-ALERT-008: `EXHAUSTED -> LOW` produces exactly one LOW alert event because the current alertable state
  changed.
- AC-ALERT-009: simultaneous transitions in distinct windows produce one event per transitioned window in
  normalized snapshot order.

### UC-ALERT-003 — Deduplicate and re-arm

- AC-ALERT-010: repeated eligible snapshots with `LOW -> LOW` produce no additional alert.
- AC-ALERT-011: repeated eligible snapshots with `EXHAUSTED -> EXHAUSTED` produce no additional alert.
- AC-ALERT-012: `LOW/EXHAUSTED -> AVAILABLE` emits no alert but updates state so a later transition into LOW
  or EXHAUSTED alerts again.
- AC-ALERT-013: temporary absence of a previously observed window does not itself re-arm or reset that
  window's remembered state.
- AC-ALERT-014: process restart creates a new silent baseline and does not require persisted deduplication
  state.

### UC-ALERT-004 — Respect notification settings

- AC-ALERT-015: when `notifications_enabled` is false, alertable transitions cause no notification-delivery
  attempt.
- AC-ALERT-016: transition tracking still advances while notifications are disabled.
- AC-ALERT-017: re-enabling notifications does not replay a transition that occurred while disabled.
- AC-ALERT-018: after re-enabling, a subsequent new alertable transition is delivered normally.

### UC-ALERT-005 — Ignore ineligible refresh outcomes

- AC-ALERT-019: stale snapshots produce no alert and do not advance remembered per-window state.
- AC-ALERT-020: refresh failures produce no alert and do not advance remembered per-window state.
- AC-ALERT-021: after stale/error outcomes, the next current snapshot is compared with the last eligible
  remembered state rather than with stale/error presentation state.

### UC-ALERT-006 — Deliver desktop notifications safely

- AC-ALERT-022: each emitted `AlertEvent` carries window id, label, current state, remaining fraction, and
  optional reset timestamp from normalized data.
- AC-ALERT-023: the desktop adapter receives no raw provider payload or credential material.
- AC-ALERT-024: a notification-delivery failure does not change the successfully refreshed usage result or
  tray/view state.
- AC-ALERT-025: a notification-delivery failure does not prevent later refreshes or later independent
  notification attempts.
- AC-ALERT-026: the target Linux notification adapter presents distinguishable LOW and EXHAUSTED
  notifications with the affected window identified.

## Architectural invariants

- INV-ALERT-001: alert transition evaluation imports no Qt, GI/Ayatana, D-Bus, subprocess, or infrastructure
  implementation.
- INV-ALERT-002: `UsageWindow.state(policy)` remains the sole LOW/EXHAUSTED classifier.
- INV-ALERT-003: no alert threshold duplicates `AppSettings.low_remaining_threshold`.
- INV-ALERT-004: notification adapters consume normalized `AlertEvent` values, never raw provider payloads.
- INV-ALERT-005: deduplication state is runtime-only and is not added to settings schema v1.
- INV-ALERT-006: notification failure is isolated from the usage refresh success/failure contract.

## Open implementation decision

The exact Linux notification transport is intentionally not selected by this requirement. Before production
implementation, inspect the available Qt/Linux mechanisms against these constraints:

1. works in the installed `uv tool` environment;
2. does not contaminate the main environment with distro-native GI dependencies;
3. works on the target Ubuntu/GNOME/Wayland workstation;
4. supports a narrow, testable adapter;
5. failure can be contained without affecting refresh.

If choosing the transport creates a lasting platform/compatibility dependency, record it in a new ADR before
the adapter is considered complete.

## Validation disposition

Not yet validated. This document is the normative basis for v1.2 TDD.
