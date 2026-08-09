# CodexBar

CodexBar is a Linux tray application that reads Codex usage/rate-limit information from the locally
authenticated Codex app-server and presents remaining quota at a glance.

## Current project status

Current release: **1.3.0**.

Validated on Ubuntu/GNOME/Wayland:
- `REQ-USAGE-001` — real Codex usage provider: **validated**.
- `REQ-UI-001` — adaptive Linux tray interaction: **validated**.
- `REQ-UI-002` — project-owned icon, native Ayatana label and Qt fallback: **validated**.
- `REQ-DESKTOP-001` — user-local installation, autostart and uninstall: **validated**.
- `REQ-SETTINGS-001` — persistent settings and runtime application: **validated**.
- `REQ-ALERT-001` — transition-based LOW/EXHAUSTED desktop alerts: **validated**.
- `REQ-HISTORY-001` — bounded local normalized usage history: **validated**.

CodexBar 1.3.0 is the validated **Remember** release: bounded local normalized usage history is now part of the supported product contract.

## Prerequisites

Required:
- Linux;
- authenticated local Codex installation;
- compatible Python version from `pyproject.toml`;
- `uv`;
- `notify-send` for desktop alerts.

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install libnotify-bin
```

Optional native Ayatana menu/label:

```bash
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

PyGObject remains outside the uv-managed environment.

## Install and run

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
"$(uv tool dir --bin)/codexbar" desktop status
"$(uv tool dir --bin)/codexbar" --gui
```

## Settings and alerts

Open **Settings** from the tray menu to edit:
- LOW remaining threshold;
- automatic refresh interval;
- notifications enabled.

Alert behavior:
- first observation is a silent baseline;
- `AVAILABLE -> LOW` alerts;
- `LOW -> EXHAUSTED` alerts;
- unchanged LOW/EXHAUSTED states are deduplicated;
- recovery to AVAILABLE re-arms a later alert;
- re-enable does not replay a transition that occurred while disabled;
- stale/error outcomes do not create alert transitions.

CLI settings:

```bash
codexbar settings show
codexbar settings reset
```

## Usage history

The v1.3 implementation stores every eligible `Freshness.CURRENT` normalized snapshot in a local
schema-v1 SQLite database. STALE fallback data is never inserted as a new historical observation.

Default history location:

```text
$XDG_DATA_HOME/codexbar/history.sqlite3
```

with host-user fallback:

```text
$HOME/.local/share/codexbar/history.sqlite3
```

Snap-scoped XDG data paths are rejected in favor of the host-user fallback.

History policy:
- fixed 30-day retention;
- observations strictly older than `now_utc - 30 days` are pruned;
- the exact cutoff observation is retained;
- history is discrete observation data, not continuous token accounting;
- history failures are isolated from successful current usage and alerts;
- raw provider payloads, account identifiers and credentials are not persisted.

Inspection and maintenance:

```bash
codexbar history inspect
codexbar history clear
```

`history clear` is destructive for stored observations but preserves the valid database schema. It is
idempotent, does not modify settings, and is not used as implicit recovery for corrupt/unsupported storage.

## Development and release checks

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

Notification diagnostics:

```bash
uv run python scripts/diagnose_notifications.py
```

History validation:

```bash
uv run python scripts/validate_history.py all
```

## Documentation map

- `CHANGELOG.md` — release history.
- `CONSTITUTION.md` — engineering rules and invariants.
- `PRODUCT_SPEC.md` — product baseline and release evolution.
- `docs/specs/v1.3/` — v1.3 history requirement and release gates.
- `docs/TRACEABILITY-REQ-HISTORY-001.md` — detailed v1.3 traceability.
- `docs/VALIDATION-REQ-HISTORY-001.md` — v1.3 target validation.
- `docs/adr/ADR-007-history-persistence.md` — SQLite/XDG persistence decision and as-built architecture.
- `docs/INSTALLATION.md` — installation, history data and troubleshooting.
- `docs/GIT_WORKFLOW.md` — repository workflow and release gates.
- `docs/RELEASE-CHECKLIST-v1.3.0.md` — final v1.3.0 release-close checklist.

Earlier release-specific traceability and validation records remain authoritative for v1.0-v1.2.

## Security boundary

CodexBar does not manage Codex credentials. Notification events and history persistence consume normalized
domain data only; raw provider payloads, account identifiers and credentials do not cross those boundaries.

## Roadmap

v1.3 is a data-foundation release: **Remember**.

Explicitly deferred beyond v1.3:
- usage-rate analytics and trend summaries;
- prediction/forecasting;
- historical charts/dashboard;
- richer visualization of current state;
- cloud/remote history;
- account-level analytics.

The next product design phase should use the v1.3 history read model rather than redefining observation
semantics.
