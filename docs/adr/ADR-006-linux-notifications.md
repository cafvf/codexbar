# ADR-006 — Linux desktop notification transport

Status: accepted, revised after target validation
Date: 2026-08-08
Revised: 2026-08-09
Release: v1.2
Requirement: REQ-ALERT-001

## Context

v1.2 needs passive desktop notifications while preserving the existing Python/uv and architecture
boundaries.

The first decision selected direct `org.freedesktop.Notifications` calls through `PySide6.QtDBus`.
Automated tests validated the abstract adapter contract, but physical Ubuntu/GNOME/Wayland validation
exposed a binding-level marshalling defect:

- the freedesktop `Notify` method requires signature `(susssasa{sv}i)`;
- PySide6 serialized the Python arguments as `(sisssava{sv}i)`;
- `replaces_id=0` became D-Bus INT32 instead of UINT32;
- an empty Python actions list became `array<variant>` instead of `array<string>`;
- GNOME correctly rejected the call with `org.freedesktop.DBus.Error.InvalidArgs`.

Continuing with QtDBus would require binding-specific manual type construction for values that are trivial
for a native notification client.

## Revised decision

Use the distro-native `notify-send` client from `libnotify-bin` as the Linux implementation of
`NotificationPort`.

The adapter invokes `notify-send` with an argument vector (never a shell string), captures the exit status,
and normalizes execution/timeout/non-zero failures to `NotificationDeliveryError`.

LOW uses normal urgency. EXHAUSTED uses critical urgency. Both retain distinct titles and the normalized
window label/body.

## Rationale

- `notify-send` is purpose-built to send desktop notifications through the user's notification daemon.
- libnotify owns the D-Bus marshalling details, including UINT32 and typed empty arrays.
- no GI/PyGObject dependency is introduced into the uv-managed environment.
- `subprocess` is confined to the infrastructure adapter; domain/application alert logic remains unchanged.
- argument-vector execution avoids shell parsing/injection.
- the external executable boundary is easy to diagnose (`command -v notify-send`, direct control call) and
  failure-isolated through the existing `NotificationPort`.

## Rejected alternatives

### Direct PySide6.QtDBus

Rejected after target validation. It works for discovery calls such as `GetServerInformation`, but the
Python binding did not preserve the exact freedesktop `Notify` types for UINT32 and an empty string array.
The resulting call was rejected by GNOME with `InvalidArgs`.

### GI/libnotify inside the uv environment

Rejected because it would reverse the existing distro-binding isolation policy.

### Generic shell command

Rejected. The adapter executes a fixed argument vector directly with `subprocess.run`; it does not invoke a
shell.

## Consequences

- Linux notification support now has a small host dependency: `notify-send` / `libnotify-bin`.
- installation documentation must list this dependency for v1.2.
- missing executable, timeout, and non-zero exit are non-fatal notification failures.
- a future platform can implement `NotificationPort` differently.
