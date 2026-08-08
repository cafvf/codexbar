# Validation record — 2026-08-08

## REQ-USAGE-001 — closed validation cycle

### Repository/container checks
- automated suite: passed before REQ-UI-001 work.
- `python -m compileall -q src`: passed.
- deterministic CLI `--mock`: passed.
- app-server protocol behavior is covered by deterministic transport tests and sanitized fixtures.

### Target-system evidence
The project owner subsequently reported successful execution on the target Linux workstation using `uv`,
including:
- the complete automated test suite;
- compilation check;
- deterministic mock execution; and
- a successful real conversation with the locally installed, authenticated Codex app-server.

Interpretation: REQ-USAGE-001 is validated end-to-end on the intended environment. This evidence is
user-reported and was not independently reproduced inside the repository validation container.

## REQ-UI-001 — current cycle

### Checks executed in this implementation environment
- `python -m pytest -ra` -> 34 passed, 1 skipped.
- skipped test: `tests/gui/test_tray_smoke.py`, because PySide6 is not installed in this container.
- `python -m compileall -q src` -> passed.
- `PYTHONPATH=src python -m codexbar --mock` -> passed.
- `PYTHONPATH=src python -m codexbar --mock --gui` -> normalized dependency error and exit code 2,
  as expected when PySide6 is absent.

### Target-system validation still required
Run with the GUI extra installed:

```bash
uv sync --extra dev --extra gui
uv run pytest -ra
uv run python -m codexbar --gui
```

Then verify that the tray icon appears, click toggles the panel, Refresh updates without freezing the
shell, stale/error presentation is sensible, and Quit shuts the process down cleanly.

## Release interpretation
REQ-USAGE-001 is validated. REQ-UI-001 implementation is present and its headless/controller acceptance
suite is green, but the Qt/Linux desktop validation gate remains open. Desktop autostart/packaging remains
outstanding for v1.0.

## REQ-UI-001 — target feedback and correction
The first target Linux GUI validation succeeded for tray presence, Show, panel rendering and Quit, but
revealed a failure of AC-UI-006: primary click opened the context menu instead of toggling the panel.
The Qt shell was changed so the context menu is no longer registered with `QSystemTrayIcon`; `Trigger`
toggles the panel and `Context` manually pops the menu. Target revalidation is required because GNOME
tray activation support varies by shell/extension.

## REQ-UI-002 — current implementation
- project-owned terminal-style tray icon implemented;
- canonical glance string implemented (`5h: X% · W: Y%`);
- missing windows are omitted rather than fabricated;
- Qt fallback exposes the glance string in the tooltip;
- native text physically adjacent to the icon is not claimed by the Qt backend and requires a dedicated
  Linux indicator backend/capability evaluation.

## Target desktop regression — adaptive tray interaction
Observed on the target Linux desktop after the manual-context-menu experiment:
- project-owned icon rendered successfully;
- primary/single click produced no usable activation;
- double click opened the details panel;
- with no registered tray menu there was no reliable tray Quit path, and the panel itself had no Quit action.

Disposition: REQ-UI-001 remains open for target validation. The Qt shell now restores a registered context
menu as the portable control surface, places live glance usage directly in that menu, maps both `Trigger`
and `DoubleClick` to the details panel where those events are delivered, and provides Quit from both the
menu and the details panel. This design follows capability-based desktop behavior rather than assuming all
Qt activation reasons are emitted by every Linux shell.


## REQ-UI-001 — target acceptance complete
The adaptive tray correction was revalidated on the target Linux desktop. Primary activation opens the
registered menu containing the live weekly percentage and explicit Open details/Quit actions. Open details
shows the usage panel with Refresh and Quit. Both shutdown paths are usable. REQ-UI-001 is therefore
accepted for the target desktop capability set rather than requiring an unavailable Qt Trigger event.

## REQ-UI-002 — native-label cycle
Ayatana AppIndicator was selected as the optional native Linux backend because it provides a dynamic
`set_label(label, guide)` API specifically suited to changing numerical status. The implementation detects
PyGObject/Ayatana system bindings at runtime and falls back to QSystemTrayIcon when absent. Automated tests
cover capability detection and label publication without requiring the system bindings. Physical rendering
of the adjacent label remains a target-desktop validation item because the indicator specification permits
desktop visualizations to omit labels.

## REQ-UI-002 — target PyGObject packaging failure and architecture correction
The first target attempt to install `codexbar[native-indicator]` through uv compiled PyGObject 3.48.2
from PyPI against Python 3.14.4 and failed because the expected `girepository.h` header layout did not
match the target distro environment. The same workstation successfully imports distro-provided `gi` from
`/usr/lib/python3/dist-packages/gi/__init__.py` using system Python 3.14.4.

Disposition: this is treated as an architecture/dependency issue rather than an application regression.
ADR-003 removes PyGObject from uv dependency resolution and hosts Ayatana in a minimal `/usr/bin/python3`
helper. The uv process now performs a system-Python capability probe and falls back to the already validated
Qt tray when native bindings are unavailable. The remaining target gate is to verify helper selection,
menu actions, dynamic adjacent label rendering, and clean shutdown on the workstation.


## REQ-UI-002 — target native-helper invisible-indicator regression
Target execution of `uv run python -m codexbar --gui` after ADR-003 left the main process running but
produced no visible tray indicator; the process had to be terminated from the terminal. This exposed a
supervision defect: capability detection proved only that system Python could import GI/Ayatana, while the
main process selected the native backend without waiting for proof that the helper had completed indicator
registration. It also lacked runtime failover if the helper subsequently exited.

Disposition: native selection now requires an explicit JSONL `ready` handshake within a bounded startup
interval. Failure or timeout causes immediate selection of the already validated Qt backend. While running,
helper liveness is monitored; unexpected helper termination activates the Qt tray fallback instead of leaving
CodexBar alive without a control surface. Target desktop revalidation remains required.

## Native indicator diagnostic gate
After target validation showed the supervised Ayatana helper falling back to Qt, a dedicated diagnostic CLI
was added. Run `uv run python -m codexbar --diagnose-indicator` and record every PASS/FAIL line. A fully
passing diagnostic establishes only that the system-Python/GI/Ayatana/GTK API path completes through one
bounded GLib-loop turn; it does not establish that the desktop shell physically renders the indicator.


## REQ-UI-002 — Snap/VS Code runtime contamination diagnosis
Target `--diagnose-indicator` execution from the VS Code integrated terminal passed `gi-import`, `ayatana-import` and `gtk-import`, then failed before helper diagnostic completion with a dynamic-loader error referencing `/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0` and missing `__libc_pthread_init@GLIBC_PRIVATE`. The identical diagnostic completed successfully from a normal terminal outside VS Code. This establishes inherited Snap runtime variables as the root cause rather than missing GI/Ayatana packages.

The parent now sanitizes the environment before every `/usr/bin/python3` probe/helper/diagnostic launch. Target revalidation is pending from the integrated VS Code terminal; success criterion is that the native backend reaches `ready` (or at minimum the diagnostic completes) without loading Snap runtime libraries, while Qt fallback remains intact if native registration still fails for desktop-shell reasons.


## REQ-UI-002 — target acceptance complete

Target workstation: Ubuntu/GNOME/Wayland.

Observed validation sequence:
1. Qt project icon and adaptive menu/detail/quit behavior were validated.
2. The initial native-helper attempt exposed Snap/IDE runtime contamination: `/usr/bin/python3` inherited
   incompatible Snap library paths and failed before native indicator readiness.
3. Running outside the VS Code/Snap-contaminated terminal confirmed that GI/Ayatana itself was healthy.
4. The launcher was changed to sanitize native-helper environment variables before process start while
   preserving Wayland/X11 and D-Bus session variables.
5. The same `uv run python -m codexbar --gui` command was then revalidated successfully from the previously
   problematic environment.
6. The native indicator rendered the available weekly percentage in the desktop bar and retained the
   expected menu behavior.

Disposition: **REQ-UI-002 validated and closed on the target environment.**

The target provider exposed the weekly window during the physical validation. The two-window string
`5h: X% · W: Y%` is therefore acceptance-tested deterministically but was not physically observed with two
simultaneously reported windows during this validation.

## Current release state

- REQ-USAGE-001: validated.
- REQ-UI-001: validated.
- REQ-UI-002: validated.
- REQ-DESKTOP-001: open; no supported system-wide installer/autostart/uninstall flow exists yet.

The repository is currently usable through the source-based `uv` workflow documented in `README.md` and
`docs/INSTALLATION.md`.
