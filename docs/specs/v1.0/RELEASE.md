# Release 1.0 — Usable Linux Codex Monitor

## Goal
Deliver a tray application that displays verified Codex usage information safely and refreshes it.

## In scope
REQ-USAGE-001, REQ-UI-001, REQ-UI-002, and minimal Linux desktop packaging/autostart required for normal use.

## Out of scope
History/graphs/advanced alerts; developer dashboard; plugin system; generic system metrics.

## Current status
- REQ-USAGE-001: implemented and validated end-to-end on the target Linux workstation.
- REQ-UI-001: implemented; first target validation exposed primary-click/context-menu regression; correction implemented and revalidation pending.
- REQ-UI-002: implemented for project icon + canonical glance formatter + Qt tooltip fallback; target validation and native adjacent-label backend evaluation pending.
- REQ-DESKTOP-001: not yet implemented.

## Release gates
1. Real source contract verified and recorded in ADR-002. **Met.**
2. Contract fixtures captured with sensitive fields removed. **Met.**
3. REQ-USAGE-001 automated and authenticated target-system validation pass. **Met.**
4. REQ-UI-001 corrected primary-click behavior passes on the target Linux desktop. **Open.**
5. REQ-UI-002 icon and glance presentation pass on the target Linux desktop; capability for a native adjacent text label is recorded. **Open.**
6. Package installs/starts without development dependencies and provides a reversible autostart path.
   **Open.**

### Tray target-desktop note
REQ-UI-001 uses capability-based tray activation. Direct primary-click detail toggling is supported when
Qt emits `Trigger`; otherwise the registered tray menu is the immediate glance/control surface. Target
revalidation of this adaptive behavior is required before the requirement is closed.
