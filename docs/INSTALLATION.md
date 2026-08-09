# Installation, desktop integration, settings and uninstall

CodexBar 1.2 uses a user-local `uv tool` installation. The installed application does **not** depend on the
source checkout after installation.

## Prerequisites

Required:
- Linux;
- local Codex installed and authenticated;
- `uv` available on `PATH`;
- `notify-send` for v1.2 desktop alerts.

On Debian/Ubuntu-family systems:

```bash
sudo apt update
sudo apt install libnotify-bin
```

For the optional native Ayatana label/menu:

```bash
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

PyGObject remains outside the uv-managed environment.

## Install from a clone or release source tree

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
```

Equivalent manual commands:

```bash
uv tool install --force --with 'PySide6>=6.8' .
"$(uv tool dir --bin)/codexbar" desktop install
```

## Verify

```bash
command -v notify-send
"$(uv tool dir --bin)/codexbar" desktop status
"$(uv tool dir --bin)/codexbar" --gui
```

For notification diagnostics from a source/release tree:

```bash
uv run python scripts/diagnose_notifications.py
```

## Settings

Tray Settings controls:
- LOW remaining threshold — default `0.20`, valid `0 < threshold < 1`;
- refresh interval — default `60` seconds, valid `10..3600`;
- notifications enabled — default `true`.

When notifications are enabled, v1.2 emits transition-based LOW/EXHAUSTED desktop notifications.
Repeated unchanged constrained states are deduplicated.

CLI:

```bash
"$(uv tool dir --bin)/codexbar" settings show
"$(uv tool dir --bin)/codexbar" settings reset
```

Settings remain schema-v1 JSON under the canonical XDG config location.

## Autostart

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart enable
"$(uv tool dir --bin)/codexbar" desktop autostart disable
```

## Native indicator diagnostics

```bash
"$(uv tool dir --bin)/codexbar" --diagnose-indicator
```

The Ayatana helper remains isolated in system Python. Native indicator failure falls back to the Qt tray.

## Uninstall

```bash
./scripts/uninstall.sh
```

or, without the checkout:

```bash
"$(uv tool dir --bin)/codexbar" desktop uninstall
uv tool uninstall codexbar
```

Persistent settings are user data and are not removed by desktop integration cleanup.

## Development/release gate

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

`uv.lock` is versioned for reproducibility.
