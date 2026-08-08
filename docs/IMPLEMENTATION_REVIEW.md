# Implementation Review Against the Constitution

Date: 2026-08-08

## Current result
The project now has two vertical slices: REQ-USAGE-001 is implemented and target-validated, while
REQ-UI-001 is implemented through the Qt shell but still awaits target-desktop validation.

## Decisions retained

| Decision | Current form |
|---|---|
| Ports/adapters | `UsageProvider` isolates the Codex app-server adapter |
| Dynamic usage windows | no fixed five-hour/weekly fields in the domain |
| Typed boundaries | immutable dataclasses, normalized exceptions |
| Spec/TDD traceability | requirement -> AC -> test -> task -> code |
| Optional GUI dependency | core remains headless; PySide6 lives behind `gui` extra |

## REQ-UI-001 architecture

```text
QSystemTrayIcon / UsagePanel
          |
     TrayController  <---- Qt polls immutable state
          |
   ThreadPoolExecutor
          |
  RefreshCoordinator
          |
    GetCurrentUsage
          |
    UsageProvider
```

The key constraint is directional: the provider call never runs on the Qt GUI thread. `TrayController`
is framework-independent and owns the asynchronous transition `LOADING -> FRESH/STALE/ERROR`. Qt only
starts refreshes, polls completion, and renders state.

## Simplicity review
- No event bus was introduced.
- No plugin framework was introduced.
- No persistent cache was introduced; stale fallback remains process-local.
- No Qt types leak into domain/application code.
- No new background scheduler abstraction was added: one single-worker executor plus Qt timers is enough
  for the current requirement.
- Overlapping refresh calls are rejected rather than queued, preventing accidental request buildup.

## Error/input/output review
- Provider errors remain normalized below the UI boundary.
- `GuiDependencyError` makes missing PySide6 an explicit user-facing runtime error.
- `SystemTrayUnavailableError` distinguishes a missing desktop tray from a Codex/provider failure.
- `TraySettings` validates refresh and poll intervals before runtime.
- `TrayViewState` is the explicit presentation output with phases `LOADING`, `FRESH`, `STALE`, `ERROR`.

## Validation status
### Closed
- REQ-USAGE-001 automated tests.
- Real authenticated app-server interaction on the target Linux workstation, reported successful by the
  project owner.

### Open
- PySide6 smoke test in an environment with the GUI extra installed.
- Manual target-desktop validation of click/toggle, refresh responsiveness, tray availability and quit.
- Desktop installation/autostart requirement.

## Next specification slice
After REQ-UI-001 target validation, open REQ-DESKTOP-001 for installation, `.desktop` integration and
opt-in autostart. Historical storage, charts and richer notifications remain out of v1.0.


## UI correction and glanceable status — 2026-08-08
- Target Linux validation showed that registering a `QMenu` directly on `QSystemTrayIcon` can cause the shell to consume primary clicks. The shell now handles `Trigger` and `Context` explicitly and only pops the menu for the latter.
- Generic desktop imagery was replaced by a project-owned terminal-style icon; no OpenAI/ChatGPT/Codex logo is embedded.
- Presentation now carries a canonical `glance_text`, derived from normalized window duration identifiers. Known windows render as `5h` and `W`; absent windows are omitted.
- `QSystemTrayIcon` has no portable adjacent-text property. The Qt backend therefore exposes `glance_text` through its tooltip. A native Linux indicator-label backend remains an explicit capability task rather than an implicit Qt hack.

## Target-desktop tray activation correction
Target validation demonstrated that treating `QSystemTrayIcon.ActivationReason.Trigger` as a portable
Linux invariant was incorrect. On the tested desktop, removing the registered menu did not recover single
click; only double click reached the application and the reliable Quit route was lost. The shell therefore
uses an adaptive model: a registered menu is the guaranteed glance/control surface, while `Trigger` and
`DoubleClick` opportunistically open details. The details panel itself now exposes Quit. This is simpler
and safer than adding desktop-specific event hacks before REQ-UI-002/desktop-backend evaluation.

## Native Linux indicator decision

The portable Qt tray remains the baseline because it is already validated on the target Linux desktop.
For adjacent dynamic quota text, the implementation now probes for Ayatana AppIndicator at runtime and,
when available, uses its `set_label(label, guide)` capability. PyGObject and Ayatana are optional because
forcing GTK/GObject dependencies on every installation would reduce portability and make the core GUI
harder to bootstrap. The native adapter pumps the GLib main context from a short Qt timer, so the existing
Qt application/controller remains the single process and the provider refresh still executes outside the
GUI thread. If native bindings are absent, selection falls back to QSystemTrayIcon with no functional loss.

## Native indicator process isolation correction
Target installation demonstrated that compiling PyGObject from PyPI inside the uv environment is not a
stable desktop-integration strategy: the project Python (3.14.4) and distro GObject Introspection headers
were incompatible with the pinned PyGObject source layout. The system Python already exposes a working
`gi` module, so ADR-003 moves GTK/Ayatana behind a helper subprocess.

The updated structure is:

```text
PySide6 / uv main process
        |
        | JSON Lines: set_glance / quit
        v
/usr/bin/python3 native_indicator_helper.py
        |
        +-- python3-gi
        +-- Gtk 3
        +-- AyatanaAppIndicator3
        |
        ^ JSON Lines: refresh / details / quit
```

This adds one explicit process boundary but removes a more dangerous implicit ABI boundary from the uv
environment. The helper receives no Codex credentials, raw app-server responses or account data. Native
capability probing is performed by `/usr/bin/python3`; failure selects the validated Qt tray backend.
The design therefore preserves graceful degradation and keeps the core/application/domain layers unchanged.

## Native indicator diagnostics
The optional Ayatana path now has an explicit provider-independent diagnostic mode. This closes an
observability gap discovered on the target desktop: a supervised fallback tells us that native readiness
failed, but not which integration stage failed. `--diagnose-indicator` reports the system Python/helper,
GI import, Ayatana import, GTK import, indicator construction, menu binding, label set, ACTIVE status and a
bounded GLib-loop turn. The command deliberately does not claim physical shell visibility.


## Native helper runtime sanitization
Target diagnostics showed a Snap-packaged VS Code terminal could inject `/snap/core20` libraries into `/usr/bin/python3`, producing a glibc symbol-lookup failure even though GI, GTK and Ayatana were correctly installed. The helper launcher now centralizes environment construction in `sanitized_native_environment()`. Availability probes, diagnostics and the production helper all use the same sanitizer, so capability detection and execution no longer disagree merely because of inherited loader state. The sanitizer removes loader/Python/GTK/GIO override variables and `SNAP*` values while preserving graphical-session and D-Bus variables.


## REQ-UI-002 closeout
Target revalidation after environment sanitization succeeded on Ubuntu/GNOME/Wayland: the Ayatana helper
reached readiness from the previously problematic VS Code/Snap launch environment, the available weekly
percentage rendered in the desktop bar, and menu behavior remained functional. REQ-UI-002 is therefore
closed. REQ-DESKTOP-001 was subsequently specified, implemented and target-validated; the historical
sequencing note is retained only to explain why desktop integration was developed after the tray contract.


## REQ-DESKTOP-001 implementation review
The desktop layer is intentionally a small stdlib-only boundary. It owns XDG application/icon/autostart
files but not the uv tool environment itself. `uv tool` provides the isolated non-editable application
installation; CodexBar writes only marked user-local desktop artifacts. Autostart is opt-in. Uninstall
refuses to remove an unexpected desktop file occupying a managed path and never recursively deletes shared
XDG directories. No repository path is embedded in the generated desktop entry. See ADR-004.


## v1.0 closeout
REQ-DESKTOP-001 completed target validation on Ubuntu/GNOME/Wayland, including canonical user-local
installation from a Snap-contaminated VS Code terminal, installed GUI execution, checkout independence,
autostart enable/disable, clean uninstall, reinstall and explicit removal of the legacy Snap-scoped tool.
All v1.0 requirement gates are closed. Release metadata is aligned to 1.0.0 and the intended annotated Git
tag is `v1.0.0`.
