# REQ-ALERT-001 — Transition-based desktop usage alerts

Status: validated
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
- `LOW`;
- `EXHAUSTED`.

`AVAILABLE` is not itself alertable.

### Baseline

The first eligible current snapshot observed after application startup establishes the runtime comparison
baseline. Establishing a baseline SHALL NOT emit an alert, even if a window is already LOW or EXHAUSTED.

### Transition

For a stable `UsageWindowId`, an alertable transition occurs when the previous eligible state and current
eligible state differ and the current state is alertable.

- `AVAILABLE -> LOW`: alert LOW;
- `AVAILABLE -> EXHAUSTED`: alert EXHAUSTED;
- `LOW -> EXHAUSTED`: alert EXHAUSTED;
- `EXHAUSTED -> LOW`: alert LOW;
- `LOW/EXHAUSTED -> AVAILABLE`: no alert; re-arm;
- unchanged LOW/EXHAUSTED: no repeated alert.

### Eligible snapshot

Only a successfully obtained `Freshness.CURRENT` snapshot is eligible to establish or advance alert state.
Stale cached snapshots and refresh errors do not establish, advance, reset or re-arm alert state.

## Scope decisions

- `notifications_enabled` is the only alert enable/disable setting.
- LOW classification uses the configured `UsagePolicy`; no duplicate threshold exists.
- EXHAUSTED remains `remaining == 0` under existing domain semantics.
- Each window is tracked independently by stable `UsageWindowId`.
- Multiple windows may generate multiple alert events in one snapshot.
- Deduplication state is process-local and not persisted.
- Restart establishes a new silent baseline.
- Newly appearing windows establish a silent baseline.
- Temporary absence does not imply recovery.
- Disabled notifications suppress delivery while transition tracking continues.
- Re-enable does not replay transitions observed while disabled.
- Settings schema v1 remains unchanged.
- Raw provider payloads and account identifiers do not cross the alert boundary.

## Alert event contract

`AlertEvent` contains normalized:
- window id;
- label;
- current `UsageWindowState`;
- remaining fraction;
- optional reset timestamp.

It contains no credentials, raw provider payloads or UI-framework objects.

## Architecture

Dependency direction:

`UsageSnapshot + UsagePolicy -> transition evaluator -> AlertEvent -> NotificationPort -> Linux adapter`

The transition evaluator remains framework-independent. `UsageWindow.state(policy)` remains the sole
classification rule.

The final Linux transport decision is recorded in ADR-006: the production adapter invokes distro-native
`notify-send` (`libnotify-bin`) through a fixed subprocess argument vector. Subprocess usage remains confined
to infrastructure.

## Failure policy

Expected delivery failures are normalized as `NotificationDeliveryError` and contained.

A delivery failure SHALL NOT:
- convert a valid usage snapshot into refresh failure;
- discard the last valid display;
- stop later refreshes;
- terminate the tray process;
- mutate usage-window state.

No automatic retry policy is introduced in v1.2.

## Acceptance criteria

All AC-ALERT-001..026 are satisfied by the automated suite plus target validation recorded in
`docs/VALIDATION-REQ-ALERT-001.md`.

See the detailed mapping in `docs/TRACEABILITY-REQ-ALERT-001.md`.

## Architectural invariants

- INV-ALERT-001: alert transition evaluation imports no platform implementation.
- INV-ALERT-002: `UsageWindow.state(policy)` remains the sole LOW/EXHAUSTED classifier.
- INV-ALERT-003: no alert threshold duplicates `AppSettings.low_remaining_threshold`.
- INV-ALERT-004: adapters consume normalized `AlertEvent`, never raw provider payloads.
- INV-ALERT-005: deduplication state is runtime-only and does not change settings schema v1.
- INV-ALERT-006: notification failure is isolated from the usage refresh contract.

## Validation disposition

Validated on Ubuntu/GNOME/Wayland.

Automated acceptance/unit/architecture/regression tests passed, along with ruff, strict mypy and compileall.
Physical validation confirmed that LOW and EXHAUSTED notifications are visibly delivered by the final
`notify-send` adapter and identify the affected usage window.

REQ-ALERT-001 is closed.
