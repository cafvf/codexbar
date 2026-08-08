# ADR-003 — Isolate Ayatana/PyGObject in a system-Python helper

Status: accepted  
Date: 2026-08-08

## Context
REQ-UI-002 needs an optional Linux-native indicator label (`5h: X% · W: Y%`). Ayatana AppIndicator
provides the required label API through GObject Introspection. The target workstation provides a working
`gi` module at `/usr/lib/python3/dist-packages` under system Python 3.14.4, while the uv-managed project
environment is intentionally isolated from distro site-packages.

Attempting to satisfy this integration by declaring `PyGObject` as a PyPI dependency caused uv to build
PyGObject from source. On the target system that build failed against the installed GObject Introspection
headers. This couples application dependency resolution to distro-specific native ABI/layout details and is
not acceptable for the primary Python environment.

## Decision
CodexBar SHALL keep its main process inside the uv-managed environment and SHALL NOT depend on PyGObject
from PyPI. The optional Ayatana integration SHALL execute as a separate helper using `/usr/bin/python3`,
thereby consuming the distro-provided `python3-gi`, GTK and Ayatana bindings.

The process boundary is intentionally narrow:

```text
uv/PySide6 main process                 /usr/bin/python3 helper
-----------------------                 ----------------------
set_glance(text, guide)  -- JSONL -->  Ayatana set_label/menu
quit                     -- JSONL -->  shutdown
refresh/details/quit     <-- JSONL --  user intent events
```

The helper SHALL NOT receive Codex credentials, provider objects, raw app-server responses or account
identifiers. It receives presentation strings only. Importability of the bindings is not sufficient evidence
that an indicator was registered successfully: after spawning, the parent SHALL require an explicit `ready`
handshake within a bounded interval. If startup does not become ready, CodexBar SHALL use the already
validated Qt tray backend. If a previously-ready helper exits while CodexBar is running, the parent SHALL
activate the Qt tray fallback at runtime.

## Consequences
### Positive
- uv dependency resolution remains pure-Python/Qt and reproducible.
- Native GNOME/GTK bindings are owned by the Linux distribution that built them.
- Failure of the optional native integration does not prevent the application from using the Qt fallback.
- A helper that imports successfully but cannot register a visible indicator is not treated as healthy merely because its process was spawned.
- GTK/GLib and Qt no longer share one Python interpreter/event loop.

### Trade-offs
- A small subprocess and JSONL protocol are introduced.
- Native-indicator availability now depends on `/usr/bin/python3` plus distro packages.
- Packaging must install the helper source alongside the Python package.

## Rejected alternatives
1. **PyGObject from PyPI inside uv** — rejected after a real target-system build failure and because it
   unnecessarily couples uv to native GNOME build prerequisites.
2. **uv environment with `system-site-packages`** — rejected because it weakens environment isolation and
   reproducibility for the whole application.
3. **Remove native label support** — rejected because REQ-UI-002 explicitly values glanceable adjacent
   usage text and Ayatana provides a suitable optional capability.

## Diagnostic observability amendment
The helper boundary SHALL provide a provider-independent diagnostic mode invoked from the main CLI as
`--diagnose-indicator`. The main process invokes the same `/usr/bin/python3` helper with `--diagnose`; the
helper emits JSONL diagnostic records for each integration stage. This mode SHALL not access Codex,
credentials or account data.

A completed Ayatana API path is not equivalent to physical shell visibility. Diagnostics therefore stop at
a bounded successful GLib-loop turn and report that visual rendering still requires target-desktop
observation. This distinction prevents the project from treating a successful API call as proof that GNOME
(or another shell) actually surfaced the indicator.

## Runtime environment sanitization amendment
Target validation exposed a second isolation concern: when CodexBar is launched from a Snap-packaged VS Code integrated terminal, inherited loader variables can cause `/usr/bin/python3` to load `/snap/core20/.../libpthread.so.0` together with the host glibc, failing before helper Python code runs with a `GLIBC_PRIVATE` symbol lookup error. The same native diagnostic succeeds from a normal system terminal.

Therefore, every system-Python probe, diagnostic invocation and production helper launch SHALL receive a sanitized environment prepared by the parent process. The sanitizer preserves the normal graphical-session/D-Bus environment but removes `LD_LIBRARY_PATH`, `PYTHONHOME`, `PYTHONPATH`, `GTK_PATH`, `GIO_EXTRA_MODULES`, `GIO_MODULE_DIR`, `GI_TYPELIB_PATH` and all `SNAP`/`SNAP_*` variables. `PYTHONUNBUFFERED=1` is then set explicitly for the JSONL protocol.

This sanitization MUST happen in the parent before `exec`/`Popen`. Removing these variables inside `native_indicator_helper.py` is insufficient because the ELF dynamic loader selects shared libraries before the Python interpreter executes the helper module.


## Target validation outcome
The sanitization amendment was revalidated on the target Ubuntu/GNOME/Wayland workstation from the same
VS Code/Snap environment that had previously triggered the glibc failure. The production GUI then selected
the native indicator successfully, rendered the available weekly percentage in the desktop bar and retained
the expected menu behavior. The Qt fallback remains required for capability or runtime failure.
