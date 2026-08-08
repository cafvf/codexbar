# REQ-UI-002 — Tray identity and glanceable usage

Status: validated on target Linux workstation  
Priority: P0  
Release: v1.0

## Requirement
CodexBar SHALL have a project-owned tray identity and SHALL make the currently reported short-window and
weekly remaining quotas available at a glance, without fabricating missing windows.

## Scope decisions
- CodexBar SHALL use project-owned artwork rather than third-party product branding.
- The canonical glance string is composed from reported windows, e.g. `5h: 73% · W: 41%`.
- Values represent remaining percentage and are rendered as whole percentages.
- Missing windows are omitted rather than rendered as zero.
- The Qt backend SHALL publish the glance string in the tray tooltip.
- Because the portable `QSystemTrayIcon` API exposes icon/tooltip/menu rather than a persistent adjacent
  text label, the registered menu SHALL also expose the live glance string as its first disabled line.
- On Linux, CodexBar SHALL prefer an Ayatana AppIndicator backend when the system bindings are available.
- Ayatana/PyGObject SHALL be consumed through a separate `/usr/bin/python3` helper using distro-provided bindings; PyGObject SHALL NOT be a PyPI dependency of the uv-managed main process.
- The native backend SHALL expose the canonical glance string through the indicator label using a stable label guide.
- The helper SHALL receive presentation data and UI intent only; Codex credentials, raw provider payloads and account identifiers SHALL NOT cross the helper boundary.
- If the system-Python/Ayatana capability probe fails, CodexBar SHALL fall back automatically to the validated Qt tray backend.
- Long text SHALL NOT be rasterized into the square icon.

### UC-UI-004 — Compact quota labels
- AC-UI-009: a canonical 300-minute window is labeled `5h`.
- AC-UI-010: a canonical 10080-minute window is labeled `W`.
- AC-UI-011: two reported windows render in source order, e.g. `5h: X% · W: Y%`.
- AC-UI-012: if only one known window is reported, only that window is rendered.

### UC-UI-005 — Tray glance surfaces
- AC-UI-013: the Qt tray tooltip contains the current canonical glance string.
- AC-UI-014: the registered tray menu's summary line contains the same canonical glance string.
- AC-UI-015: stale data remains visible and is explicitly marked stale instead of being discarded.

## Validation gate — portable path closed
The project icon, dynamic menu glance and adaptive interaction were validated on the target desktop.
The native Ayatana path was subsequently validated after the helper supervision and runtime-sanitization
work described below.

### UC-UI-006 — Native Linux adjacent label
- AC-UI-016: when Ayatana bindings are available to `/usr/bin/python3`, CodexBar selects the native indicator backend.
- AC-UI-017: the native indicator receives the canonical glance string as its dynamic label.
- AC-UI-018: the label guide reserves enough width for `5h: 100% · W: 100% · stale`.
- AC-UI-019: when Ayatana is unavailable, the Qt backend remains usable without error.
- AC-UI-020: the uv-managed project has no PyGObject runtime dependency.
- AC-UI-021: availability is probed using the system Python rather than importing `gi` in the main process.
- AC-UI-022: main-to-helper messages contain only presentation commands (`set_glance`, `quit`).
- AC-UI-023: helper-to-main events are limited to UI intents (`refresh`, `details`, `quit`).
- AC-UI-024: native-helper failure at capability selection does not prevent Qt fallback.
- AC-UI-025: native selection is accepted only after the helper emits an explicit `ready` handshake within a bounded startup interval.
- AC-UI-026: if a selected helper exits after startup, CodexBar activates the Qt tray fallback at runtime instead of remaining alive without a visible control surface.

## System dependency and process-boundary note
The Ayatana backend is intentionally not installed from PyPI. On Debian/Ubuntu-family systems the expected
system bindings are provided by distro packages such as `python3-gi`, `gir1.2-ayatanaappindicator3-0.1` and
`gir1.2-gtk-3.0`. Availability is probed by invoking `/usr/bin/python3`. If available, a minimal helper
process hosts GTK/Ayatana and communicates with the uv/PySide6 main process over JSON Lines. See ADR-003.

## Validation gate — closed
Target validation on Ubuntu/GNOME/Wayland confirmed that, after sanitizing the native-helper launch
environment, the Ayatana backend reaches readiness, renders the available weekly percentage in the desktop
bar, and preserves the expected menu interaction. The Qt fallback had previously been validated and remains
the required safe fallback when the native helper is unavailable or unhealthy.

The observed target source exposed only the weekly window during this validation, so the single-window
presentation was validated physically. Two-window formatting (`5h: X% · W: Y%`) remains covered
deterministically by acceptance tests and will render both when both windows are reported.

### UC-UI-007 — Native indicator diagnostics
- AC-UI-027: CodexBar exposes `--diagnose-indicator` without requiring a Codex provider call.
- AC-UI-028: diagnostics report explicit steps for environment, `gi`, Ayatana, GTK, indicator creation, menu binding, label publication, ACTIVE status and at least one bounded GLib-loop turn.
- AC-UI-029: a failed diagnostic step returns a non-zero process status and identifies the failing step without disabling the normal Qt fallback path.
- AC-UI-030: a successful diagnostic explicitly states that API-path completion does not prove physical shell rendering.
- AC-UI-031: diagnostic execution uses `/usr/bin/python3` and the same isolated helper boundary defined by ADR-003.
- AC-UI-032: every `/usr/bin/python3` native probe/helper/diagnostic launch SHALL use a sanitized environment that removes external loader, Python, GTK/GIO and Snap runtime overrides while preserving the graphical-session and D-Bus variables required by the target desktop.
- AC-UI-033: the sanitization policy SHALL be regression-tested against Snap-injected `LD_LIBRARY_PATH`/`SNAP*` values and SHALL preserve `DISPLAY`/`WAYLAND_DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR` and desktop/session metadata when present.

## Diagnostic command
For target-desktop troubleshooting, run:

```bash
uv run python -m codexbar --diagnose-indicator
```

The command is intentionally provider-independent and must not contact the Codex app-server. Its purpose is
to distinguish binding/import failures from indicator construction, menu/label registration and GLib-loop
failures. Physical visibility in the desktop shell remains a separate manual acceptance check.

## Target runtime-contamination finding
Target diagnostics run inside the Snap-packaged VS Code integrated terminal passed GI/Ayatana/GTK imports but the helper then failed in the dynamic loader with `/snap/core20/.../libpthread.so.0` and a `GLIBC_PRIVATE` symbol lookup error. Running the same diagnostic from a normal system terminal completed successfully. This confirms that the helper boundary must sanitize inherited runtime variables before `/usr/bin/python3` starts; sanitizing inside the helper would be too late because the dynamic loader resolves shared libraries before Python executes user code.
