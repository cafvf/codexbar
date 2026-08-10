# CodexBar v1.4 — Target Validation

Date: 2026-08-10T10:16:29-03:00
Overall result: **PASS**

## Environment

- Platform: `Linux-7.0.0-29-generic-x86_64-with-glibc2.43`
- Python: `3.14.4`
- XDG_CURRENT_DESKTOP: `ubuntu:GNOME`
- XDG_SESSION_TYPE: `wayland`
- DISPLAY: `:0`
- WAYLAND_DISPLAY: `wayland-0`

## Automated preflight

### pytest — PASS

`uv run pytest -ra`

```text
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 61%]
........................................................................ [ 81%]
.................................................................        [100%]
353 passed in 0.81s
```

stderr:

```text
(no stderr)
```

### ruff — PASS

`uv run ruff check src tests scripts`

```text
All checks passed!
```

stderr:

```text
(no stderr)
```

### mypy — PASS

`uv run mypy`

```text
Success: no issues found in 37 source files
```

stderr:

```text
(no stderr)
```

### compileall — PASS

`uv run python -m compileall -q src scripts`

```text
(no stdout)
```

stderr:

```text
(no stderr)
```

### history inspect — PASS

`uv run codexbar history inspect`

```text
Path: /home/christiano/.local/share/codexbar/history.sqlite3
State: ready_non_empty
Schema: 1
Snapshots: 1508
Oldest: 2026-08-09T02:41:40.948562+00:00
Newest: 2026-08-10T13:01:37.140903+00:00
```

stderr:

```text
(no stderr)
```

### native indicator diagnostics — PASS

`uv run codexbar --diagnose-indicator`

```text
CodexBar native indicator diagnostics
[PASS] system-python — /usr/bin/python3
[PASS] helper — /home/christiano/git/codexbar/src/codexbar/ui/native_indicator_helper.py
[PASS] environment — desktop=ubuntu:GNOME; session=wayland; display=True; wayland=True
[PASS] gi-import — /usr/lib/python3/dist-packages/gi/__init__.py
[PASS] ayatana-import
[PASS] gtk-import
[PASS] indicator-create
[PASS] menu-bind
[PASS] label-set
[PASS] status-active
[PASS] glib-loop — 250 ms loop completed; physical shell rendering is not asserted
Result: native indicator API path completed; physical shell rendering still requires visual validation.
```

stderr:

```text
[stderr] (native_indicator_helper.py:2835085): libayatana-appindicator-WARNING **: 10:01:37.999: libayatana-appindicator is deprecated. Please use libayatana-appindicator-glib in newly written code.
Gtk-Message: 10:01:38.028: Failed to load module "canberra-gtk-module"
```

## Manual target-system checks

1. **PASS — Rich current panel opens** (required)
   - Procedure: Launch `uv run codexbar --gui`, open details, and confirm the enriched CURRENT panel is visible.
2. **PASS — Current cards show expected fields** (required)
   - Procedure: Confirm each reported window shows label, whole percent, progress bar, AVAILABLE/LOW/EXHAUSTED state, and reset data when available.
3. **PASS — CURRENT and STALE are distinguishable** (conditional)
   - Procedure: Confirm CURRENT is explicit during normal operation. If a STALE state is safely reproducible, confirm the last valid values remain visible and STALE is clearly indicated.
4. **PASS — Observation age updates** (required)
   - Procedure: Confirm the detail panel shows the observation timestamp and a plausible elapsed age derived from the current snapshot.
5. **PASS — Reset presentation is coherent** (conditional)
   - Procedure: For a window with reset metadata, confirm the Reset text shows both absolute time and relative duration. If the card says `Reset: not reported`, mark this check SKIP.
6. **PASS — Current-to-history navigation preserves identity** (required)
   - Procedure: Click View history on a CURRENT card and confirm History opens focused on the same usage window, not merely a matching label.
7. **PASS — Current refresh remains responsive** (required)
   - Procedure: Open History, close/hide it, trigger CURRENT Refresh, then repeat with History visible. Confirm CodexBar remains running, the current panel stays responsive, and values update normally.
8. **PASS — History remains functional** (required)
   - Procedure: Open History and confirm retained observations, 24h/7d/30d period switching, explicit time-axis semantics, and discrete observations.
9. **PASS — Ayatana path remains functional** (required)
   - Procedure: Confirm the native Ayatana indicator still shows the canonical glance and exposes Refresh, Open details, History, Settings, Quit.
10. **SKIP — Qt fallback remains functional** (conditional)
   - Procedure: When the Qt fallback path is available, confirm tray, details, History, Settings, Refresh, and Quit remain usable.
   - Note: Qt fallback not tested

## v1.4 target gate

The v1.4 target gate closes only when automated preflight is green and all required manual checks pass.
Conditional checks may be skipped when the corresponding runtime state/path is not safely available, with justification.
