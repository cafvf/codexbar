# Installation and first run

This document describes the **current source-based installation**. A normal end-user installer/package is
not yet part of the validated release; that work belongs to `REQ-DESKTOP-001`.

## 1. Prerequisites

1. Linux with a local Codex installation.
2. Codex already authenticated locally.
3. `uv` installed.
4. A Python version accepted by `pyproject.toml`.

For the optional native Ayatana indicator on Debian/Ubuntu-family systems:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

Do not add `pygobject` to the uv environment. Native GTK/Ayatana integration deliberately uses
`/usr/bin/python3` plus distro bindings.

## 2. Clone

```bash
git clone <repository-url>
cd codexbar
```

## 3. Resolve the development environment

```bash
uv sync --extra dev --extra gui --extra native-indicator
```

`uv.lock` is committed to the repository and should be used as the reproducible dependency resolution.

## 4. Verify before first real run

```bash
uv run pytest -ra
uv run python -m compileall -q src
uv run python -m codexbar --mock
```

For GUI smoke testing without the real provider:

```bash
uv run python -m codexbar --mock --gui
```

## 5. Run against the authenticated Codex installation

CLI:

```bash
uv run python -m codexbar
```

Tray GUI:

```bash
uv run python -m codexbar --gui
```

The application prefers the native Ayatana backend when it reaches its readiness handshake. Otherwise it
must fall back to the Qt tray automatically.

## 6. Diagnose native indicator problems

```bash
uv run python -m codexbar --diagnose-indicator
```

A successful API diagnostic does not by itself prove that the desktop shell physically renders the label;
physical visibility is a target-desktop acceptance property.

The native helper is launched with a sanitized environment. In particular, Snap/IDE variables that can
inject incompatible libraries are removed before `/usr/bin/python3` starts, while graphical-session and
D-Bus variables are preserved.

## 7. Stopping a development run

Prefer the tray/menu **Quit** action. If a broken development build cannot expose Quit, return to the
terminal and press `Ctrl+C`. As a last resort, identify and terminate the process:

```bash
pgrep -af codexbar
kill <pid>
```

## Current limitation

There is no supported system-wide installation, `.desktop` file, autostart installer or uninstall command
yet. Do not document ad-hoc copies into `/usr/local`, `~/.local/bin` or autostart directories as official
installation. Those behaviors will be specified and tested in `REQ-DESKTOP-001`.
