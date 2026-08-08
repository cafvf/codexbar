# Release 1.0 — Usable Linux Codex Monitor

## Goal
Deliver a tray application that displays verified Codex usage information safely and refreshes it.

## In scope
REQ-USAGE-001, REQ-UI-001, REQ-UI-002, and minimal Linux desktop packaging/autostart required for normal use.

## Out of scope
History/graphs/advanced alerts; developer dashboard; plugin system; generic system metrics.

## Current status
- REQ-USAGE-001: implemented and validated end-to-end on the target Linux workstation.
- REQ-UI-001: accepted on the target Linux workstation using the adaptive registered-menu interaction.
- REQ-UI-002: **validated** on the target Ubuntu/GNOME/Wayland workstation, including the sanitized system-Python Ayatana helper, native weekly label rendering, menu interaction and Qt fallback.
- REQ-DESKTOP-001: not yet implemented.

## Release gates
1. Real source contract verified and recorded in ADR-002. **Met.**
2. Contract fixtures captured with sensitive fields removed. **Met.**
3. REQ-USAGE-001 automated and authenticated target-system validation pass. **Met.**
4. REQ-UI-001 adaptive tray behavior passes on the target Linux desktop. **Met.**
5. REQ-UI-002 icon and Qt glance presentation pass on the target Linux desktop; system-Python native adjacent-label helper physically renders as specified. **Met.**
6. Package installs/starts without development dependencies and provides a reversible autostart path.
   **Open.**

### Tray target-desktop note
REQ-UI-001 uses capability-based tray activation. Direct primary-click detail toggling is supported when
Qt emits `Trigger`; otherwise the registered tray menu is the immediate glance/control surface. Target
revalidation of this adaptive behavior is required before the requirement is closed.

### Native tray-label increment
REQ-UI-001 has passed target-desktop acceptance using the adaptive registered-menu interaction. REQ-UI-002
now includes an optional Ayatana AppIndicator backend hosted in a `/usr/bin/python3` helper, while retaining
the validated Qt fallback. This prevents PyGObject/GTK ABI dependencies from entering the uv environment.
Target validation confirmed native weekly-label rendering after environment sanitization. REQ-UI-002 is closed; REQ-DESKTOP-001 is the next open release gate.
