# CodexBar Product Specification

Status: v1.0 normative

## Purpose
Provide a small Linux desktop monitor that makes the Codex usage information available at a glance,
without requiring the user to enter the interactive CLI solely to inspect usage.

## Product truth
CodexBar reports **what a verified Codex source exposes**. It does not promise an absolute token
balance unless the source explicitly provides that quantity. Usage windows are dynamic data.

## Core user outcome
The user can see current remaining usage, reset times when supplied, freshness, and whether the
reported windows indicate an exhausted limiting quota.

## Stable domain vocabulary
- Usage window: one independently reported quota/rate-limit window.
- Remaining fraction: normalized value in `[0,1]`.
- Snapshot: immutable observation of all windows at a point in time.
- Freshness: whether displayed data is current or cached/stale.
- Limiting window: a window whose valid state prevents continued included usage, when such semantics
  are known from the source contract.

## v1.0 scope
1. Query a verified local Codex source through an adapter.
2. Normalize one or more usage windows.
3. Display remaining fraction and reset time.
4. Preserve last valid snapshot during transient refresh failure and mark it stale.
5. Run as a Linux tray application with a compact panel.

## Non-goals for v1.0
Historical charts, generic developer dashboard, LM Studio/system metrics, plugin architecture, remote
account management, credit purchasing, and prediction of future consumption.

## Non-functional requirements
- Core must be usable without GUI dependencies.
- Domain and application layers are deterministic and independently testable.
- Unknown source schema fails closed.
- UI refresh must not block the GUI thread.
- User-facing timestamps are localized; internal timestamps remain timezone-aware.
- Optional distro-native desktop bindings SHALL NOT contaminate the uv-managed main environment; native Ayatana integration is isolated behind a system-Python helper and capability fallback.
- No credentials or raw Codex provider payloads SHALL cross the native-helper IPC boundary.

## Risks
The Codex usage surface may change independently of CodexBar. A CLI text parser is especially fragile;
therefore source selection and fixture provenance are release gates rather than hidden assumptions.


## Current validated baseline
As of the REQ-UI-002 closeout:
- real Codex usage retrieval is validated on the target Linux workstation;
- adaptive Qt tray interaction is validated;
- native Ayatana glance rendering is validated on Ubuntu/GNOME/Wayland with a sanitized system-Python helper;
- Qt remains the mandatory fallback when the native helper is unavailable or unhealthy;
- source-based use through `uv` is supported and documented;
- user-local `uv tool` installation, XDG `.desktop`, opt-in autostart and managed uninstall are validated end-to-end under REQ-DESKTOP-001.

A new user cloning the repository SHALL be able to discover the supported source-based setup from
`README.md` without relying on conversation history.


## Distribution and desktop integration
The v1.0 supported installation mechanism is user-local `uv tool` installation plus CodexBar-managed XDG
artifacts. Installation SHALL not require the checkout after completion, SHALL not install development
dependencies, SHALL leave autostart disabled by default and SHALL provide a reversible uninstall path. See
REQ-DESKTOP-001 and ADR-004.

## v1.0 release state
REQ-USAGE-001, REQ-UI-001, REQ-UI-002 and REQ-DESKTOP-001 are validated on the target Linux workstation.
All release gates defined in `docs/specs/v1.0/RELEASE.md` are closed.
