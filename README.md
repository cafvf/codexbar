# CodexBar

CodexBar is a Linux tray application that reads Codex usage/rate-limit information from the locally
authenticated Codex app-server and presents remaining quota at a glance.

## Current project status

Current release: **1.2.0**.

Validated on Ubuntu/GNOME/Wayland:
- `REQ-USAGE-001` — real Codex usage provider: **validated**.
- `REQ-UI-001` — adaptive Linux tray interaction: **validated**.
- `REQ-UI-002` — project-owned icon, native Ayatana label and Qt fallback: **validated**.
- `REQ-DESKTOP-001` — user-local installation, autostart and uninstall: **validated**.
- `REQ-SETTINGS-001` — persistent settings and runtime application: **validated**.
- `REQ-ALERT-001` — transition-based LOW/EXHAUSTED desktop alerts: **validated**.

CodexBar 1.2.0 preserves the v1.0/v1.1 baseline and adds real transition-based desktop notifications.

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

Alert behavior in v1.2:
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

## Documentation map

- `CHANGELOG.md` — release history.
- `CONSTITUTION.md` — engineering rules and invariants.
- `PRODUCT_SPEC.md` — product baseline.
- `docs/specs/v1.2/` — v1.2 alert requirement and release gates.
- `docs/TRACEABILITY-REQ-ALERT-001.md` — detailed v1.2 traceability.
- `docs/VALIDATION-REQ-ALERT-001.md` — v1.2 target validation.
- `docs/adr/ADR-006-linux-notifications.md` — final Linux notification transport decision.
- `docs/INSTALLATION.md` — installation and troubleshooting.
- `docs/GIT_WORKFLOW.md` — repository workflow.

## Security boundary

CodexBar does not manage Codex credentials. Notification events contain normalized window state only; raw
provider payloads, account identifiers and credentials do not cross the notification boundary.

## Roadmap

The v1.2 scope is closed. Later candidates include usage history/charts, additional desktop targets and
packaging formats; none are part of the v1.2 contract.
