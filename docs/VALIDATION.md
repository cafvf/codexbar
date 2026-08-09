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
toggles the panel and `Context` manually pops the menu. This historical failure was superseded by the adaptive registered-menu design, which was later validated on the target desktop.

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
CodexBar alive without a control surface. This historical failure was later closed by bounded readiness, runtime supervision and Qt fallback, followed by successful target validation.

## Native indicator diagnostic gate
After target validation showed the supervised Ayatana helper falling back to Qt, a dedicated diagnostic CLI
was added. Run `uv run python -m codexbar --diagnose-indicator` and record every PASS/FAIL line. A fully
passing diagnostic establishes only that the system-Python/GI/Ayatana/GTK API path completes through one
bounded GLib-loop turn; it does not establish that the desktop shell physically renders the indicator.


## REQ-UI-002 — Snap/VS Code runtime contamination diagnosis
Target `--diagnose-indicator` execution from the VS Code integrated terminal passed `gi-import`, `ayatana-import` and `gtk-import`, then failed before helper diagnostic completion with a dynamic-loader error referencing `/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0` and missing `__libc_pthread_init@GLIBC_PRIVATE`. The identical diagnostic completed successfully from a normal terminal outside VS Code. This establishes inherited Snap runtime variables as the root cause rather than missing GI/Ayatana packages.

The parent now sanitizes the environment before every `/usr/bin/python3` probe/helper/diagnostic launch.
This historical gate was subsequently revalidated successfully from the integrated VS Code terminal; the
native backend reached readiness and rendered the weekly label while the Qt fallback remained available.


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
- REQ-DESKTOP-001: validated end-to-end on the target Ubuntu/GNOME/Wayland workstation.

The repository is currently usable through the source-based `uv` workflow documented in `README.md` and
`docs/INSTALLATION.md`.


## REQ-DESKTOP-001 — implementation validation

Automated implementation checks cover XDG path resolution, absolute installed-launcher references,
idempotent installation, opt-in/reversible autostart, managed-file ownership protection, status reporting
and preservation of unrelated XDG files. The normal installer uses `uv tool install` with PySide6 and does
not request the development extra.

Target validation remains open and must confirm: clean user-local install, desktop-menu launch, tray
behavior, installed-launcher operation after the checkout is renamed/removed, autostart enable/disable and
clean uninstall. Until those steps pass, the v1.0 release gate remains open.

### REQ-DESKTOP-001 implementation-environment result
- `python -m pytest -ra` -> **75 passed, 1 skipped**.
- skipped test: optional Qt GUI smoke because PySide6 is not installed in this execution environment.
- `python -m compileall -q src` -> passed.
- `sh -n scripts/install.sh scripts/uninstall.sh` equivalent syntax checks -> passed individually.
- an XDG-temporary-directory CLI simulation completed install -> status -> autostart enable -> status -> uninstall and left an unrelated file intact.
- `ruff` and `mypy` were not available in this execution environment; the target development environment should run them through the committed `dev` extra before release tagging.

### REQ-DESKTOP-001 quality-gate correction
Target development validation reported 77 passing tests but exposed two release-gate defects: repository-wide
`ruff` violations and `mypy` treating the installed `codexbar` package as untyped because no `py.typed`
marker/configuration directed it to the source tree. The corrective patch makes the declared quality gates
real rather than advisory: formatting/import/modernization violations identified by the target run are
corrected, `src/codexbar/py.typed` is packaged, and mypy is configured to check `src/codexbar` directly in
strict mode. Target rerun of `uv run ruff check src tests` and `uv run mypy` remains required before the
clean-install acceptance sequence continues.

### REQ-DESKTOP-001 quality-gate correction — strict typing follow-up
A second target quality-gate run kept the functional suite green (77 passed) and narrowed the remaining
failures to strict static-analysis integration points: subprocess text-pipe typing, a Qt method-name override
collision (`UsagePanel.render` vs `QWidget.render`), nullable Qt layout items, QByteArray-to-bytes typing,
`QApplication.instance()` narrowing, obsolete `type: ignore` comments, and one test file resource-lifetime
warning. The corrective patch resolves these without weakening `mypy --strict` or excluding files from
`ruff`.

The supported Python range is also made explicit as `>=3.12,<3.15`. Python 3.12–3.14 are the intended v1.0
range; Python 3.15+ is not claimed until separately validated. The target must rerun pytest, ruff, mypy and
compileall before continuing to installation acceptance.

### REQ-DESKTOP-001 — Snap-scoped installation regression
The first target install was launched from a Snap-packaged VS Code terminal. `HOME` remained the real user
home, but VS Code exported `XDG_DATA_HOME=$HOME/snap/code/<revision>/.local/share`. Because uv derives its
default tool location from XDG data paths, the initial install placed both the uv tool and XDG desktop
assets below the VS Code Snap sandbox.

Disposition: the supported installer now pins the canonical host-user XDG/uv paths
(`$HOME/.local/share`, `$HOME/.config`, `$HOME/.local/bin`, `$HOME/.local/share/uv/tools`). Desktop path
resolution also rejects XDG data/config homes below `$HOME/snap/`. A previously created Snap-scoped tool is
reported for explicit cleanup after the canonical installation is validated; it is never deleted
automatically.

## REQ-DESKTOP-001 — target acceptance complete

Target workstation: Ubuntu/GNOME/Wayland.

The release candidate completed the full desktop-distribution acceptance cycle:
- the repository quality gates were exercised during release hardening;
- `scripts/install.sh` installed a canonical user-local uv tool, desktop entry and icon;
- `~/.local/bin/codexbar desktop status` reported Installed/Launcher/Desktop entry/Icon as healthy and
  autostart disabled;
- the installed GUI/tray ran successfully;
- after temporarily renaming the checkout, the installed launcher continued to run, proving checkout
  independence;
- autostart enable, status and disable completed successfully;
- `scripts/uninstall.sh` removed the canonical installation;
- checks confirmed removal of launcher, desktop entry, icon and autostart artifact;
- reinstall restored a healthy application with autostart disabled;
- the earlier legacy uv tool under the VS Code Snap-scoped XDG path was explicitly removed;
- the canonical installation remained healthy afterward.

Disposition: **REQ-DESKTOP-001 validated and closed.**

## v1.0 release disposition
All four v1.0 requirements are validated on the target Linux workstation. Package/release metadata is
aligned to `1.0.0`. The remaining release procedure is repository hygiene: run the final automated gates,
review the staged diff, commit the release changes, verify a clean working tree and create annotated tag
`v1.0.0`.
## v1.1 — REQ-SETTINGS-001 release disposition

Target workstation: Ubuntu/GNOME/Wayland.

`REQ-SETTINGS-001` completed the specification-first implementation and target validation cycle. Automated
gates passed at the implementation gate (`pytest`, `ruff`, strict `mypy`, `compileall`). Physical validation
covered opening current settings, Save, live LOW-threshold/refresh application, Cancel, validation feedback,
Reset, CLI inspection/reset and persistence across process restart.

Target validation exposed one backend-parity defect: the Qt tray menu exposed Settings while the active
Ayatana helper menu initially did not. The native helper intent contract and menu were corrected so both
backends expose the Settings surface.

The refresh interval domain was reconciled explicitly with the normative specification: `10..3600` seconds
inclusive. Values near 3500 are valid; 3601 is invalid.

Disposition: **REQ-SETTINGS-001 validated and closed.**

Before creating the v1.1.0 tag, rerun the final release gates from `docs/GIT_WORKFLOW.md`. The final gate run
belongs to release hygiene; it does not reopen the already completed requirement unless it finds a regression.
