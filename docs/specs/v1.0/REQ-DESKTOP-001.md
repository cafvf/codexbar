# REQ-DESKTOP-001 — User-local Linux desktop installation

Status: validated on target Linux workstation  
Priority: P0  
Release: v1.0

## Requirement
CodexBar SHALL provide a reproducible, user-local and reversible Linux installation path that does not
require the source checkout after installation, does not require root privileges for CodexBar-owned files,
and does not enable autostart without explicit user action.

## Scope decisions
- The supported v1.0 distribution mechanism is `uv tool install` from a source checkout or release source.
- Runtime GUI dependency PySide6 is installed into the uv-managed tool environment; development extras are not.
- Distro-native GI/Ayatana dependencies remain system packages and are not installed from PyPI.
- Desktop integration follows XDG user directories: applications/icon data under `XDG_DATA_HOME` and
  autostart under `XDG_CONFIG_HOME`, with standard home-directory fallbacks.
- The `.desktop` launcher SHALL reference the installed `codexbar` executable, never the repository checkout.
- Autostart is opt-in and independently reversible.
- Uninstall SHALL remove only CodexBar-owned XDG artifacts; removal of the uv tool itself is a separate,
  explicit `uv tool uninstall codexbar` operation.
- v1.0 SHALL not require `sudo` for CodexBar application files. System package installation for optional
  Ayatana support is outside CodexBar's ownership boundary.

### UC-DESKTOP-001 — Install desktop integration
- AC-DESKTOP-001: the generated application entry references an absolute installed launcher and contains no checkout path dependency.
- AC-DESKTOP-002: installation creates a user-local `.desktop` entry and project-owned scalable icon.
- AC-DESKTOP-003: repeating installation is idempotent.
- AC-DESKTOP-004: installation leaves autostart disabled by default.

### UC-DESKTOP-002 — Manage autostart
- AC-DESKTOP-005: enabling autostart creates a managed user-session autostart entry using the installed launcher.
- AC-DESKTOP-006: disabling autostart is safe and idempotent.

### UC-DESKTOP-003 — Status and uninstall
- AC-DESKTOP-007: status reports launcher, application entry, icon and autostart state independently.
- AC-DESKTOP-008: desktop uninstall removes CodexBar-managed application/autostart/icon files.
- AC-DESKTOP-009: uninstall refuses to remove an unexpected/unmanaged desktop file at a managed path.
- AC-DESKTOP-010: unrelated files in shared XDG directories are preserved.

### UC-DESKTOP-004 — Distribution workflow
- AC-DESKTOP-011: the supported install script installs the tool without development dependencies and then installs XDG integration.
- AC-DESKTOP-012: the supported uninstall script removes XDG integration before removing the uv tool.
- AC-DESKTOP-013: after installation, normal execution does not require the original checkout to exist.

## Target validation gate — closed
The target Ubuntu/GNOME/Wayland workstation completed the full acceptance sequence:

1. canonical user-local install from a VS Code/Snap terminal;
2. `desktop status` reported launcher, desktop entry and icon installed with autostart disabled;
3. installed GUI/tray execution succeeded;
4. installed execution remained functional after the source checkout was temporarily renamed;
5. autostart enable/status/disable succeeded;
6. uninstall removed CodexBar-owned integration and tool files;
7. clean reinstall restored the application successfully;
8. the earlier Snap-scoped legacy tool was explicitly removed while the canonical installation remained
   functional.

Disposition: AC-DESKTOP-001..016 are accepted for the target environment and REQ-DESKTOP-001 is closed.

## Development/release quality constraints
- The v1.0 source tree SHALL pass the committed repository-wide `ruff` configuration without excluding
  pre-existing production or test files merely to make the gate green.
- The `codexbar` package SHALL be checked with `mypy` in strict mode and SHALL ship a `py.typed` marker.
- Static-analysis defects at Qt/subprocess boundaries SHALL be resolved by explicit typing/narrowing rather
  than broad `ignore_errors` or blanket `type: ignore` suppression.
- The supported Python interval for v1.0 is `>=3.12,<3.15`; later Python versions require a separate
  compatibility validation before being advertised.

### UC-DESKTOP-005 — Host user-directory isolation
- AC-DESKTOP-014: if the installer or desktop commands inherit an `XDG_DATA_HOME` or `XDG_CONFIG_HOME`
  located below `$HOME/snap/`, CodexBar SHALL ignore that sandbox-scoped value and use the canonical
  host-user locations `$HOME/.local/share` and `$HOME/.config`.
- AC-DESKTOP-015: the supported install script SHALL set `UV_TOOL_DIR=$HOME/.local/share/uv/tools` and
  `UV_TOOL_BIN_DIR=$HOME/.local/bin` explicitly so uv tool placement does not inherit a Snap-scoped XDG
  environment.
- AC-DESKTOP-016: detection of a previous Snap-scoped CodexBar tool SHALL be reported to the user but
  SHALL NOT be removed automatically.
