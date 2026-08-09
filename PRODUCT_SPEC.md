# CodexBar Product Specification

Status: v1.1 normative

## Purpose
Provide a small Linux desktop monitor that makes Codex usage information available at a glance without
requiring the user to enter the interactive CLI solely to inspect usage, while allowing user-visible
monitoring behavior to be configured without source-code changes.

## Product truth
CodexBar reports **what a verified Codex source exposes**. It does not promise an absolute token balance
unless the source explicitly provides that quantity. Usage windows are dynamic data.

## Core user outcome
The user can see current remaining usage, reset times when supplied, freshness, and whether reported windows
indicate an exhausted limiting quota. The user can persist and restore supported monitoring preferences.

## Stable domain vocabulary
- Usage window: one independently reported quota/rate-limit window.
- Remaining fraction: normalized value in `[0,1]`.
- Snapshot: immutable observation of all windows at a point in time.
- Freshness: whether displayed data is current or cached/stale.
- Limiting window: a window whose valid state prevents continued included usage, when such semantics are
  known from the source contract.
- App settings: validated persistent user configuration that feeds existing domain policy rather than
  replacing it.

## v1.0 baseline
1. Query a verified local Codex source through an adapter.
2. Normalize one or more usage windows.
3. Display remaining fraction and reset time.
4. Preserve the last valid snapshot during transient refresh failure and mark it stale.
5. Run as a Linux tray application with a compact panel.
6. Support user-local installation, XDG desktop integration, opt-in autostart and managed uninstall.

## v1.1 scope
1. Persist schema-versioned user settings in the canonical host-user XDG configuration location.
2. Configure the existing LOW-state policy through `AppSettings -> UsagePolicy`.
3. Configure automatic refresh cadence without process restart or overlapping refresh operations.
4. Persist future notification enablement without implementing notification delivery.
5. Expose settings inspection/reset through CLI and edit/save/cancel/reset through the GUI.
6. Recover safely from malformed or unsupported persisted settings.

Normative details are in `docs/specs/v1.1/REQ-SETTINGS-001.md`.

## Non-goals through v1.1
Historical charts, generic developer dashboard, LM Studio/system metrics, plugin architecture, remote account
management, credit purchasing, prediction of future consumption, notification delivery/deduplication, native
package distribution, and arbitrary CLI mutation of individual settings.

## Non-functional requirements
- Core must be usable without GUI dependencies.
- Domain and application layers are deterministic and independently testable.
- Unknown source and settings schemas fail closed.
- UI refresh must not block the GUI thread.
- Automatic refreshes must not overlap.
- User-facing timestamps are localized; internal timestamps remain timezone-aware.
- Optional distro-native desktop bindings SHALL NOT contaminate the uv-managed main environment.
- No credentials or raw Codex provider payloads SHALL cross the native-helper IPC boundary.
- Persistent settings SHALL not create a second source of truth for usage classification.
- Persistence-format evolution requires an explicit compatibility decision.

## Distribution and desktop integration
The supported installation mechanism remains user-local `uv tool` installation plus CodexBar-managed XDG
artifacts. Installation does not require the checkout after completion, does not install development
dependencies, leaves autostart disabled by default and provides a reversible uninstall path.

## Current validated baseline
Validated on Ubuntu/GNOME/Wayland:
- `REQ-USAGE-001`;
- `REQ-UI-001`;
- `REQ-UI-002`;
- `REQ-DESKTOP-001`;
- `REQ-SETTINGS-001`.

The native Ayatana helper remains optional and capability-driven; Qt remains the fallback. Persistent settings
were validated through automated tests and physical open/edit/save/cancel/reset/restart behavior on the target
workstation.

## v1.1 release state
All requirements scoped by `docs/specs/v1.1/RELEASE.md` are validated. Version metadata is prepared for
`1.1.0`; the remaining release operation is final gate execution, release commit and annotated tag creation.
