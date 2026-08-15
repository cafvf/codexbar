# Installation and lifecycle

The **canonical public installation procedure** is maintained in the root
[`README.md`](../README.md#installing-codexbar-on-ubuntu).

This file intentionally does not duplicate the full command sequence. Keeping one
installation authority avoids divergence between release instructions.

## Supported public path

The supported installation model is:

1. Linux, with Ubuntu/GNOME as the validated physical target;
2. a locally installed and authenticated Codex CLI/app-server;
3. Python in the range declared by `pyproject.toml`;
4. `uv` on `PATH`;
5. a released CodexBar source tag;
6. `./scripts/install.sh`, which installs a user-local `uv tool`.

For the current validated release, follow the README and select `v1.8.0` before
running the installer. Do not use `sudo pip` or install CodexBar into the system
Python interpreter.

## Verification

After installation, the public verification path is:

```bash
CODEXBAR="$(uv tool dir --bin)/codexbar"

"$CODEXBAR" desktop status
"$CODEXBAR" doctor
"$CODEXBAR" --diagnose-indicator
"$CODEXBAR" --gui
```

`--diagnose-indicator` checks the optional native Ayatana path; physical tray
rendering still requires a real desktop session.

## Upgrade

Select the desired released tag in the source checkout and rerun:

```bash
./scripts/install.sh
```

The installer replaces application code through `uv tool install --force`.
Normal persistent user data is not intentionally removed by an upgrade.

## Uninstall and retained data

With the source checkout:

```bash
./scripts/uninstall.sh
```

Without it:

```bash
"$(uv tool dir --bin)/codexbar" desktop uninstall
uv tool uninstall codexbar
```

Uninstall removes the installed application and desktop integration but
intentionally **preserves user data**. In particular, settings, usage History,
and the reset event ledger are not silently destroyed.

To remove retained History deliberately:

```bash
"$(uv tool dir --bin)/codexbar" history clear
```

For a complete local-data purge, first stop CodexBar and inspect the exact
CodexBar-specific paths reported by its diagnostics/inspection commands. Remove
only CodexBar-specific files or directories; never delete broad XDG roots such as
`~/.config` or `~/.local/share`.

## Development setup

Development dependencies and release gates are documented separately in the
README and `docs/GIT_WORKFLOW.md`. Development setup is not part of the public
installation contract.
