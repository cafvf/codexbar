# CodexBar

CodexBar is a Linux tray application that reads Codex usage/rate-limit information from the locally
authenticated Codex app-server and presents the remaining quota at a glance.

## Current project status

Current release: **1.1.0**.

Validated on the target Ubuntu/GNOME/Wayland workstation:

- `REQ-USAGE-001` — real Codex usage provider: **validated**.
- `REQ-UI-001` — adaptive Linux tray interaction: **validated**.
- `REQ-UI-002` — project-owned icon, glanceable quota presentation, Ayatana native label and Qt fallback: **validated**.
- `REQ-DESKTOP-001` — user-local installation, XDG desktop integration, opt-in autostart and uninstall: **validated**.
- `REQ-SETTINGS-001` — persistent settings, runtime application and GUI lifecycle: **validated**.

CodexBar 1.1.0 preserves the v1.0 provider/domain/desktop baseline and adds validated persistent user
settings.

## Prerequisites

Required:

- Linux;
- a working local Codex installation already authenticated;
- Python compatible with the version declared in `pyproject.toml`;
- [uv](https://docs.astral.sh/uv/).

GUI:

- PySide6 is installed by the `gui` extra.

Optional native adjacent-label backend on Debian/Ubuntu-family systems:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

PyGObject is intentionally **not** installed into the uv environment. The Ayatana integration runs in a
small helper using `/usr/bin/python3` and distro-provided `gi` bindings. See
`docs/adr/ADR-003-native-indicator-helper.md`.

## Install and run

For normal use from a clone or release source tree:

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
```

Then verify and start the installed application:

```bash
"$(uv tool dir --bin)/codexbar" desktop status
"$(uv tool dir --bin)/codexbar" --gui
```

The installer uses `uv tool install` with PySide6 and **without development dependencies**, installs a
user-local `.desktop` entry and project icon, and leaves autostart disabled. The installed application does
not depend on the source checkout. See `docs/INSTALLATION.md`.

## Settings

Open **Settings** from the tray menu to edit:

- LOW remaining threshold — default `0.20`, valid domain `0 < threshold < 1`;
- automatic refresh interval — default `60` seconds, valid domain `10..3600` seconds;
- notifications enabled — persisted now; actual notification delivery is deferred to `REQ-ALERT-001`.

Inspect or reset settings without the GUI:

```bash
codexbar settings show
codexbar settings reset
```

Settings are persisted as schema-v1 JSON under `XDG_CONFIG_HOME/codexbar/settings.json`, falling back to
`$HOME/.config/codexbar/settings.json`. Corrupt or unsupported documents fall back to defaults with a
diagnostic instead of preventing startup.

## Development from the repository

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
uv run python -m codexbar --gui
```

## Installation environment isolation

The supported desktop installer pins canonical user-local locations under `$HOME/.local` and `$HOME/.config`.
This is intentional: Snap-packaged IDEs may override XDG paths inside their sandbox. Running
`scripts/install.sh` from such a terminal must still produce the same host-user installation.

## Native-indicator diagnostics

If the GUI starts but the native indicator is not visible, run:

```bash
uv run python -m codexbar --diagnose-indicator
```

The diagnostic checks the system Python, GI/Ayatana/GTK imports, indicator creation, menu/label publication
and the native event loop. The helper is launched with a sanitized environment so Snap/IDE runtime library
paths cannot override the host glibc/GTK stack. If native startup fails, the normal application remains
usable through the Qt fallback.

## Development checks

Before committing:

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
git status
```

`uv.lock` **is versioned**. `.venv/`, caches, build outputs and generated local artifacts are not.

See `docs/GIT_WORKFLOW.md` for repository hygiene and `AGENTS.md` for the specification/TDD workflow.

## Documentation map

- `CHANGELOG.md` — released changes by version.
- `LICENSE` — MIT license.
- `CONSTITUTION.md` — engineering rules and invariants.
- `PRODUCT_SPEC.md` — current product baseline.
- `docs/specs/v1.0/` — normative v1.0 requirements and release gates.
- `docs/specs/v1.1/` — normative v1.1 settings requirement and release gates.
- `docs/tasks/v1.0/TASKS.md`, `docs/tasks/v1.1/TASKS.md` — requirement-derived implementation tasks.
- `docs/TRACEABILITY.md` — cross-release traceability summary.
- `docs/TRACEABILITY-REQ-SETTINGS-001.md` — detailed v1.1 settings traceability.
- `docs/VALIDATION.md` — cross-release validation record.
- `docs/VALIDATION-REQ-SETTINGS-001.md` — detailed v1.1 target validation.
- `docs/adr/` — architecture decisions.
- `docs/INSTALLATION.md` — installation, settings location and troubleshooting.
- `docs/GIT_WORKFLOW.md` — clone/update/branch/commit/tag rules.

## Security boundary

CodexBar does not manage Codex credentials. The main provider talks to the locally authenticated Codex
app-server. The native indicator helper receives presentation strings and UI intents only; credentials,
raw provider payloads and account identifiers must not cross the helper IPC boundary.

## Roadmap

The v1.1 scope is closed. The next planned specification is `REQ-ALERT-001`, which may add notification
delivery and deduplication on top of the persisted `notifications_enabled` preference. Usage history/charts,
native package formats and additional desktop coverage remain later candidates.
