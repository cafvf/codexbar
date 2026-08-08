# ADR-004 — User-local desktop distribution with uv tool and XDG

Status: accepted and target-validated for v1.0  
Date: 2026-08-08

## Context
REQ-USAGE-001 and the Linux tray requirements are validated when run from a repository-managed uv
environment. v1.0 additionally needs a normal user workflow that does not depend on the source checkout,
does not install development dependencies, does not require root privileges for CodexBar-owned files and
can be cleanly reversed.

CodexBar also has a deliberate split runtime: the main application belongs in its isolated Python
environment, while optional GI/Ayatana bindings come from the Linux distribution and are hosted by the
system-Python helper described in ADR-003.

## Decision
The v1.0 source/release installation mechanism SHALL be `uv tool install`.

The supported installer performs:

1. `uv tool install --force --with 'PySide6>=6.8' <source>`;
2. resolution of uv's tool executable directory;
3. execution of the installed `codexbar desktop install` command.

The installed application manages these XDG user artifacts:

- `${XDG_DATA_HOME:-~/.local/share}/applications/codexbar.desktop`;
- `${XDG_DATA_HOME:-~/.local/share}/icons/hicolor/scalable/apps/codexbar.svg`;
- `${XDG_CONFIG_HOME:-~/.config}/autostart/codexbar.desktop` only when the user explicitly enables autostart.

Desktop entries point to the absolute uv-tool launcher, never to a repository path. Generated managed
`.desktop` files contain an ownership marker so uninstall refuses to delete an unexpected file that merely
occupies the same path. Shared parent directories are never recursively removed.

Autostart is opt-in. `codexbar desktop autostart enable|disable` controls only the user-session autostart
entry.

Uninstall is intentionally two-layered:

1. `codexbar desktop uninstall` removes CodexBar-owned XDG integration;
2. `uv tool uninstall codexbar` removes the isolated application environment and launcher.

The provided `scripts/uninstall.sh` performs these in this order when a source/release tree is available.

## Rationale
`uv tool` gives the application an isolated, non-editable environment and a stable launcher without
inventing a custom Python environment layout. XDG user paths avoid requiring `sudo`, are conventional on
Linux and are easy to test with directory overrides. Keeping uv-tool removal separate avoids deleting the
interpreter/environment from inside the running process.

## Consequences
- `uv` is an installation-time and management prerequisite for v1.0 source/release distribution.
- The installed app survives deletion or movement of the original checkout.
- Development dependencies are not part of the installed tool.
- Optional distro packages for Ayatana remain an external system capability and are not installed by
  CodexBar's user-local installer.
- A future distro-native package (`.deb`, Flatpak, etc.) may supersede this mechanism but must satisfy the
  same REQ-DESKTOP-001 behavioral contracts or introduce a new ADR.

## Snap-scoped XDG isolation amendment
A target install launched from the Snap build of VS Code demonstrated that `HOME` can remain the real user
home while `XDG_DATA_HOME` is redirected into `$HOME/snap/code/<revision>/.local/share`. Letting uv and
CodexBar consume that value makes an installation depend on the IDE sandbox and even on its Snap revision.

The supported v1.0 installer therefore pins canonical host-user paths for both uv tools and XDG integration.
At runtime, CodexBar ignores XDG data/config values rooted below `$HOME/snap/` and falls back to the normal
host-user locations. Existing sandbox-scoped installs are not removed automatically because ownership and
user intent cannot be inferred safely.


## Validation outcome
The target Ubuntu/GNOME/Wayland workstation validated the complete decision: canonical installation,
desktop status, GUI launch, operation after the checkout was renamed, opt-in autostart enable/disable,
managed uninstall, clean reinstall and legacy Snap-scoped tool cleanup. The installed canonical application
remained functional after cleanup.
