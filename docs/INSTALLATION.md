# Installation, desktop integration and uninstall

CodexBar v1.0 uses a user-local `uv tool` installation. The installed application does **not** depend on the
source checkout after installation.

## Prerequisites

Required:

- Linux;
- local Codex installed and authenticated;
- `uv` available on `PATH`.

For the native Ayatana label on Debian/Ubuntu-family systems:

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

The desktop application entry is installed in the user XDG applications directory and may be launched
from the desktop's application menu.

## Autostart

Autostart is opt-in:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart enable
```

Check:

```bash
"$(uv tool dir --bin)/codexbar" desktop status
```

Disable:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart disable
```

No autostart file is created by the normal installation command.

## Checkout-independence check

After installation, the original checkout is not required. For validation, stop CodexBar, temporarily
rename the repository directory, then start the installed launcher:

```bash
mv codexbar codexbar.source-backup
"$(uv tool dir --bin)/codexbar" --gui
```

Restore the source directory afterward if you want to use the provided uninstall script:

```bash
mv codexbar.source-backup codexbar
```

## Native indicator diagnostics

```bash
"$(uv tool dir --bin)/codexbar" --diagnose-indicator
```

The system-Python helper is launched with a sanitized environment to prevent Snap/IDE runtime library
paths from contaminating the host GI/GTK stack. Native failure must fall back to the Qt tray.

## Uninstall

If you still have a source/release tree:

```bash
./scripts/uninstall.sh
```

Without the source tree, use the installed command first to remove desktop integration, then remove the uv
tool:

```bash
"$(uv tool dir --bin)/codexbar" desktop uninstall
uv tool uninstall codexbar
```

The desktop uninstall removes only CodexBar-managed application, icon and autostart files. It does not
recursively remove shared XDG directories or unrelated files.

## Development environment

Development remains separate from installation:

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run python -m compileall -q src
```

`uv.lock` is versioned for reproducibility of development and CI. The installed uv tool does not include the
`dev` extra.

## VS Code / Snap environments
The supported installer normalizes installation paths even when launched from a Snap-packaged IDE. It
installs the uv tool under `$HOME/.local/share/uv/tools`, the executable under `$HOME/.local/bin`, desktop
data under `$HOME/.local/share`, and autostart configuration under `$HOME/.config`.

If a prior development install was accidentally created below `$HOME/snap/code/<revision>/...`, the
installer reports the exact legacy `XDG_DATA_HOME` and a cleanup command. Validate the canonical install
first; cleanup is intentionally explicit rather than automatic.
