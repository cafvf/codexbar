# CodexBar Product Specification

Status: v1.2 validated baseline; v1.3 planned
Current validated release: 1.2.0

## Purpose

Provide a small Linux desktop monitor that makes Codex usage information available at a glance without
requiring the user to enter the interactive CLI solely to inspect usage, while allowing user-visible
monitoring behavior to be configured without source-code changes.

## Product truth

CodexBar reports **what a verified Codex source exposes**. It does not promise an absolute token balance
unless the source explicitly provides that quantity.

Usage history records observations made by CodexBar. It SHALL NOT imply continuous measurement, reconstruct
unobserved values, or claim that differences between observations are authoritative token-accounting data.

## Core user outcome

The user can:
- see current remaining usage and reset times when supplied;
- distinguish current from stale data;
- configure supported monitoring behavior;
- receive transition-based LOW/EXHAUSTED alerts;
- beginning in v1.3, retain normalized current observations locally for later inspection and analysis.

## Stable domain vocabulary

- **Usage window:** one independently reported quota/rate-limit window.
- **Remaining fraction:** normalized value in `[0,1]`.
- **Snapshot:** immutable observation of all windows at a point in time.
- **Freshness:** whether displayed data is current or cached/stale.
- **Limiting window:** a window whose valid state prevents continued included usage when such semantics are
  known from the source contract.
- **App settings:** validated persistent configuration feeding existing domain policy.
- **Historical snapshot:** one persisted, eligible `Freshness.CURRENT` normalized snapshot.
- **Historical window observation:** the normalized state of one usage window within a historical snapshot.

## Validated release baseline

### v1.0 — Observe
1. Query a verified local Codex source through an adapter.
2. Normalize one or more usage windows.
3. Display remaining fraction and reset time.
4. Preserve the last valid snapshot during transient refresh failure and mark it stale.
5. Run as a Linux tray application.
6. Support user-local installation, XDG integration, opt-in autostart and managed uninstall.

### v1.1 — Configure
1. Persist schema-versioned user settings.
2. Configure LOW-state policy through `AppSettings -> UsagePolicy`.
3. Configure automatic refresh cadence without restart or overlapping refresh.
4. Persist notification enablement.
5. Expose settings through CLI and GUI.
6. Recover safely from malformed/unsupported settings.

### v1.2 — Notify
1. Notify on transitions into LOW and EXHAUSTED.
2. Establish silent startup/restart baselines.
3. Deduplicate unchanged alertable states and re-arm after recovery.
4. Respect `notifications_enabled` without replay.
5. Ignore stale/error outcomes for alert transitions.
6. Isolate notification delivery failures from usage refresh.
7. Deliver Linux desktop alerts through `notify-send` / `libnotify-bin`.

Normative details:
- `docs/specs/v1.0/`
- `docs/specs/v1.1/`
- `docs/specs/v1.2/`

## Planned v1.3 — Remember

v1.3 introduces persistent **local normalized usage history**.

The release SHALL:
1. persist eligible CURRENT observations without storing raw provider payloads;
2. keep history persistence independent from settings persistence;
3. use an explicit, versioned history schema;
4. provide deterministic query semantics by time range and usage-window identity;
5. apply bounded retention;
6. contain history storage failures so current usage, tray operation and alerts remain usable;
7. expose enough inspection/maintenance behavior to validate the stored history.

`REQ-HISTORY-001` is the normative requirement.

## Explicitly deferred beyond v1.3

- usage-rate analytics;
- prediction of time to LOW/EXHAUSTED;
- consumption forecasting;
- statistical trend models;
- rich historical charts/dashboard;
- richer current-state visualization;
- cloud sync;
- remote history;
- provider raw-payload archival;
- account-level analytics;
- native Linux packaging beyond the validated uv/XDG workflow.

These capabilities may consume v1.3 history later but SHALL NOT silently expand v1.3.

## Non-functional requirements

- Core behavior remains usable without GUI dependencies.
- Domain/application behavior remains deterministic and independently testable.
- Unknown source, settings and history schemas fail closed.
- UI refresh must not block the GUI thread.
- Automatic refreshes must not overlap.
- User-facing timestamps are localized; internal/persisted timestamps remain timezone-aware.
- Distro-native desktop bindings SHALL NOT contaminate the uv-managed environment.
- Credentials and raw provider payloads SHALL NOT cross alert, native-helper or history boundaries.
- Settings SHALL not become a second source of truth for usage classification.
- History SHALL not become a second source of truth for current usage.
- Persistence-format evolution requires an explicit compatibility decision.
- Persistence failure in a secondary capability SHALL NOT fabricate source failure or stale data.

## Distribution and local data

Supported application installation remains user-local `uv tool` plus CodexBar-managed XDG artifacts.

Configuration belongs under the canonical XDG configuration location.

Historical usage is application data rather than configuration and SHALL use the canonical host-user XDG data
location. The intended v1.3 path is:

`$XDG_DATA_HOME/codexbar/history.sqlite3`

falling back to:

`$HOME/.local/share/codexbar/history.sqlite3`

The exact history storage schema requires an ADR before production implementation.

## Current validated baseline

Validated on Ubuntu/GNOME/Wayland:
- `REQ-USAGE-001`;
- `REQ-UI-001`;
- `REQ-UI-002`;
- `REQ-DESKTOP-001`;
- `REQ-SETTINGS-001`;
- `REQ-ALERT-001`.

v1.2.0 is the current validated release.
