# ADR-006 — Linux desktop notification transport

Status: accepted
Date: 2026-08-08
Release: v1.2
Requirement: REQ-ALERT-001

## Context

v1.2 introduces passive desktop notifications for normalized usage-state transitions. The transport choice
creates a lasting desktop compatibility boundary and therefore requires an ADR under C-11.

CodexBar already depends on PySide6 for the GUI, runs as a user-local `uv tool`, supports
Ubuntu/GNOME/Wayland as the validated target, and intentionally isolates distro-native GI/Ayatana bindings
in a system-Python helper.

Candidate transports considered:

1. `QSystemTrayIcon.showMessage()`;
2. spawning `notify-send`;
3. GI/libnotify bindings;
4. direct `org.freedesktop.Notifications` D-Bus calls through `PySide6.QtDBus`.

## Decision

Use the freedesktop Desktop Notifications D-Bus protocol through `PySide6.QtDBus` for the Linux notification
adapter.

The adapter will call the session-bus service `org.freedesktop.Notifications`, object path
`/org/freedesktop/Notifications`, interface `org.freedesktop.Notifications`, method `Notify`.

The application layer exposes a narrow `NotificationPort`; no Qt/D-Bus type crosses that port.

## Rationale

- `org.freedesktop.Notifications` is the desktop notification protocol rather than a tray-specific API.
- PySide6 already supplies Qt D-Bus integration in the GUI runtime, so no new Python package or distro GI
  binding is required.
- The choice is independent of whether CodexBar is currently using the native Ayatana indicator or the Qt
  tray fallback.
- Direct protocol use avoids relying on an external `notify-send` executable and subprocess lifecycle.
- The adapter can normalize D-Bus/service failures to `NotificationDeliveryError`.
- The core transition/deduplication logic remains fully framework-independent.

## Rejected alternatives

### QSystemTrayIcon.showMessage

Rejected as the primary transport because alerts are not conceptually tray messages and CodexBar may use the
Ayatana backend instead of a visible Qt tray icon. Qt also documents that tray-message presentation depends
on system support/configuration.

### `notify-send` subprocess

Rejected because it adds an executable/runtime dependency and subprocess failure surface for behavior that is
already available through the existing Qt runtime.

### GI/libnotify in the main environment

Rejected because it conflicts with the established isolation strategy: distro-native GI dependencies must not
contaminate the uv-managed main environment.

## Consequences

- The Linux adapter depends on PySide6 QtDBus availability and a freedesktop notification service on the
  user session bus.
- Transport availability/failure must be treated as non-fatal.
- Target-system validation must include the actual Ubuntu/GNOME/Wayland notification server.
- A future non-Linux port may implement `NotificationPort` differently without changing alert transition
  semantics.

## References

- freedesktop.org Desktop Notifications Specification, version 1.3.
- Qt for Python `PySide6.QtDBus.QDBusInterface` documentation.
- Qt `QSystemTrayIcon.showMessage()` documentation (considered and rejected as the primary transport).
