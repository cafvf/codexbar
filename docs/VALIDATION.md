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
