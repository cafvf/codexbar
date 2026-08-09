# CodexBar Product Specification

Status: v1.3 validated baseline
Current validated release: 1.3.0

## Purpose

Provide a small Linux desktop monitor that makes Codex usage information available at a glance without
requiring the user to enter the interactive CLI solely to inspect usage, while allowing user-visible
monitoring behavior to be configured without source-code changes.

## Product truth

CodexBar reports **what a verified Codex source exposes**. It does not promise an absolute token balance
unless the source explicitly provides that quantity.

Usage history records observations made by CodexBar. It does not imply continuous measurement, reconstruct
unobserved values, or claim that differences between observations are authoritative token-accounting data.

## Core user outcome

The user can:
- see current remaining usage and reset times when supplied;
- distinguish current from stale data;
- configure supported monitoring behavior;
- receive transition-based LOW/EXHAUSTED alerts;
- retain normalized CURRENT observations locally for bounded historical inspection;
- inspect and explicitly clear local history without coupling it to settings or current usage state.

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
- **Historical window sample:** one historical window observation together with its observation timestamp and
  normalized source context.

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

### v1.3 — Remember
1. Persist every eligible CURRENT normalized observation without raw provider payloads.
2. Store history in schema-v1 SQLite under the canonical host-user XDG data location.
3. Keep settings schema v1 and history schema v1 independent.
4. Query snapshots and stable window identities with half-open `[start, end)` semantics.
5. Retain 30 days using the exact cutoff rule `observed_at < now_utc - 30 days`.
6. Treat snapshot metadata plus all child window observations as one atomic persistence unit.
7. Keep STALE/provider-error fallbacks out of history.
8. Isolate history append/prune failures from current usage, tray state and alert evaluation.
9. Run SQLite capture/maintenance in the existing refresh worker path, not the GUI polling path.
10. Expose non-destructive `history inspect` and explicit destructive `history clear`.
11. Fail closed for corrupt/unsupported history instead of silently recreating it.
12. Preserve discrete-observation semantics: no interpolation, forecasting or fabricated intermediate usage.

Normative details:
- `docs/specs/v1.0/`
- `docs/specs/v1.1/`
- `docs/specs/v1.2/`
- `docs/specs/v1.3/REQ-HISTORY-001.md`
- `docs/adr/ADR-007-history-persistence.md`

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

These capabilities may consume v1.3 history later but SHALL NOT redefine v1.3 observation semantics.

## Non-functional requirements

- Core behavior remains usable without GUI dependencies.
- Domain/application behavior remains deterministic and independently testable.
- Unknown source, settings and history schemas fail closed.
- UI refresh must not block the GUI thread.
- Automatic refreshes must not overlap.
- User-facing timestamps are localized where rendered; persisted history timestamps use canonical
  timezone-aware UTC representation.
- Distro-native desktop bindings SHALL NOT contaminate the uv-managed environment.
- Credentials and raw provider payloads SHALL NOT cross alert, native-helper or history boundaries.
- Settings SHALL not become a second source of truth for usage classification.
- History SHALL not become a second source of truth for current usage.
- Persistence-format evolution requires an explicit compatibility decision.
- Persistence failure in a secondary capability SHALL NOT fabricate source failure or stale data.

## Distribution and local data

Supported application installation remains user-local `uv tool` plus CodexBar-managed XDG artifacts.

Configuration belongs under the canonical XDG configuration location and remains schema-v1 JSON.

Historical usage is application data and uses:

`$XDG_DATA_HOME/codexbar/history.sqlite3`

falling back to:

`$HOME/.local/share/codexbar/history.sqlite3`

Snap-scoped `XDG_DATA_HOME` values below `$HOME/snap/` fall back to the canonical host-user data location.

History schema version 1 and its compatibility policy are recorded in ADR-007 and implemented by the SQLite
infrastructure adapter.

## Current validation state

Validated on Ubuntu/GNOME/Wayland:
- `REQ-USAGE-001`;
- `REQ-UI-001`;
- `REQ-UI-002`;
- `REQ-DESKTOP-001`;
- `REQ-SETTINGS-001`;
- `REQ-ALERT-001`;
- `REQ-HISTORY-001`.

v1.3.0 is the current validated release.
