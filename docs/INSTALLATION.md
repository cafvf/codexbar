# Installation, desktop integration, settings and uninstall

CodexBar 1.1 uses a user-local `uv tool` installation. The installed application does **not** depend on the
source checkout after installation.

## Prerequisites

Required:

- Linux;
- local Codex installed and authenticated;
- `uv` available on `PATH`.

For the native Ayatana label/menu on Debian/Ubuntu-family systems:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

These are distro-native bindings. Do not install PyGObject into the uv tool environment.

## Install from a clone or release source tree

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
```

The script installs the application with PySide6 but without development/test dependencies, then creates
user-local XDG desktop integration. It does not enable autostart.

Equivalent manual commands:

```bash
uv tool install --force --with 'PySide6>=6.8' .
"$(uv tool dir --bin)/codexbar" desktop install
```

## Verify the installation

```bash
"$(uv tool dir --bin)/codexbar" desktop status
"$(uv tool dir --bin)/codexbar" --gui
```

Expected initial status includes:

```text
Installed: yes
Launcher: ok
Desktop entry: ok
Icon: ok
Autostart: disabled
```

## Settings

The GUI exposes **Settings** from the tray menu in both supported menu backends.

CLI inspection/reset:

```bash
"$(uv tool dir --bin)/codexbar" settings show
"$(uv tool dir --bin)/codexbar" settings reset
```

Managed values:
- LOW remaining threshold: default `0.20`, valid `0 < threshold < 1`;
- refresh interval: default `60` seconds, valid `10..3600` seconds;
- notifications enabled: default `true`; delivery is not implemented in v1.1.

Canonical settings file:
- `$XDG_CONFIG_HOME/codexbar/settings.json` when the host-user XDG config path is valid;
- otherwise `$HOME/.config/codexbar/settings.json`.

A malformed/unsupported settings document does not prevent startup. Defaults become effective and
`settings show` exposes the diagnostic. Reading a bad document does not silently replace it.

## Autostart

Autostart is opt-in:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart enable
```

Disable:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart disable
```

No autostart file is created by normal installation.

## Checkout-independence check

After installation, the original checkout is not required. For validation, stop CodexBar, temporarily
rename the repository directory, then start the installed launcher:

```bash
mv codexbar codexbar.source-backup
"$(uv tool dir --bin)/codexbar" --gui
```

Restore the source directory afterward if desired:

```bash
mv codexbar.source-backup codexbar
```

## Native indicator diagnostics

```bash
"$(uv tool dir --bin)/codexbar" --diagnose-indicator
```

The system-Python helper is launched with a sanitized environment to prevent Snap/IDE runtime library paths
from contaminating the host GI/GTK stack. Native failure falls back to the Qt tray.

## Uninstall

If you still have a source/release tree:

```bash
./scripts/uninstall.sh
```

Without the source tree:

```bash
"$(uv tool dir --bin)/codexbar" desktop uninstall
uv tool uninstall codexbar
```

Desktop uninstall removes only CodexBar-managed application, icon and autostart files. Persistent application
settings are user data and are not recursively deleted as part of desktop integration removal.

## Development environment

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

`uv.lock` is versioned for reproducibility. The installed uv tool does not include the `dev` extra.

## VS Code / Snap environments

The supported installer normalizes installation paths even when launched from a Snap-packaged IDE. It
installs the uv tool under `$HOME/.local/share/uv/tools`, the executable under `$HOME/.local/bin`, desktop
data under `$HOME/.local/share`, and application/autostart configuration under `$HOME/.config`.

If a prior development install was accidentally created below `$HOME/snap/code/<revision>/...`, validate the
canonical install first; cleanup is intentionally explicit rather than automatic.
