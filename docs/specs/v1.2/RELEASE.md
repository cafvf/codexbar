# CodexBar v1.2 Release Specification

Status: specification
Release target: v1.2.0
Change taxonomy: EVOLUTION

## Goal

Add useful desktop alerts for meaningful Codex usage-state transitions without turning periodic refresh
into repeated notification noise and without weakening the v1.0/v1.1 provider, domain, settings, desktop,
or failure-safety contracts.

## Scoped requirements

- `REQ-ALERT-001` — transition-based desktop usage alerts.

## Product intent

A user who leaves CodexBar running should be warned when a reported usage window becomes LOW or EXHAUSTED,
but should not receive the same alert on every refresh while that state remains unchanged.

The v1.1 `notifications_enabled` setting is the single user-facing enable/disable switch for this behavior.

## Release-level decisions

- Alert decisions are driven by normalized usage-window state, not raw provider payloads.
- LOW/EXHAUSTED classification continues to use the existing `UsagePolicy`; v1.2 introduces no second
  threshold.
- Notifications are transition-based and deduplicated within a running process.
- Alert state is runtime state, not durable user configuration.
- A fresh baseline observation establishes state but does not notify.
- Stale snapshots and refresh errors do not create new usage alerts.
- Notification-delivery failure is non-fatal and must not break refresh, tray operation, or the last valid
  usage display.
- v1.2 does not add alert sounds, per-window preferences, cooldown timers, notification history, or persisted
  deduplication state.

## Non-goals

- Notification history or an inbox.
- Usage history, retention, charts, or forecasting.
- Configurable LOW and EXHAUSTED alert types independently.
- Per-window notification preferences.
- User-configurable cooldown periods.
- Repeated reminders while a window remains LOW/EXHAUSTED.
- Persisting alert/deduplication state across process restart.
- Notifications for provider/network errors.
- Notifications for stale cached data.
- Native package distribution.
- Remote push/mobile/email notifications.

## Compatibility

v1.2 SHALL preserve:

- v1.0 provider and normalized usage contracts;
- v1.0 stale/error semantics and desktop installation behavior;
- v1.1 schema-v1 settings compatibility;
- v1.1 LOW-threshold configuration through `AppSettings -> UsagePolicy`;
- v1.1 refresh scheduling and no-overlap behavior;
- optional native Ayatana helper isolation.

No settings schema change is required by this release.

## Release gates

- [ ] Every `REQ-ALERT-001` acceptance criterion has automated evidence.
- [ ] Alert transition/deduplication logic is framework-independent and unit tested.
- [ ] Notification delivery is isolated behind an application-facing port/boundary.
- [ ] Existing v1.0 and v1.1 acceptance suites remain green.
- [ ] Architecture tests prove that domain/application alert logic does not import Qt or platform-specific
  notification implementations.
- [ ] Disabled notifications cause no delivery attempt while state tracking remains deterministic.
- [ ] Stale/error paths cannot fabricate LOW/EXHAUSTED transitions.
- [ ] Notification-delivery failures cannot break refresh/tray behavior.
- [ ] `ruff`, strict `mypy`, `compileall`, and repository-wide pytest pass.
- [ ] Target Linux workstation validates LOW, EXHAUSTED, deduplication, re-arm, disablement, and failure-safe
  behavior.

## Release disposition

This document defines scope only. v1.2 is not release-ready until `REQ-ALERT-001`, derived tasks, automated
evidence, traceability, and target validation are complete.
