# REQ-UI-002 — Tray identity and glanceable usage

Status: implemented / target-desktop validation pending  
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
- A future native Linux indicator backend may expose persistent adjacent text if the target desktop
  supports it cleanly; long text SHALL NOT be rasterized into the square icon.

### UC-UI-004 — Compact quota labels
- AC-UI-009: a canonical 300-minute window is labeled `5h`.
- AC-UI-010: a canonical 10080-minute window is labeled `W`.
- AC-UI-011: two reported windows render in source order, e.g. `5h: X% · W: Y%`.
- AC-UI-012: if only one known window is reported, only that window is rendered.

### UC-UI-005 — Tray glance surfaces
- AC-UI-013: the Qt tray tooltip contains the current canonical glance string.
- AC-UI-014: the registered tray menu's summary line contains the same canonical glance string.
- AC-UI-015: stale data remains visible and is explicitly marked stale instead of being discarded.

## Validation gate
The project icon has been observed successfully on the target desktop. The dynamic tooltip/menu glance
and interaction behavior remain pending target-desktop validation after the adaptive-menu correction.
