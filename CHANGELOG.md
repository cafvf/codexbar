# Changelog

## 1.2.0 — 2026-08-09

Validated alerting release of CodexBar.

### Added
- transition-based desktop notifications for LOW and EXHAUSTED Codex usage states;
- per-window runtime transition tracking with silent startup/restart baselines;
- deduplication of repeated unchanged constrained states;
- re-arm after recovery to AVAILABLE;
- live respect for the persisted `notifications_enabled` setting without replay on re-enable;
- `NotificationPort` boundary and normalized `NotificationDeliveryError`;
- Linux desktop notification delivery through distro-native `notify-send` / `libnotify-bin`;
- controlled alert-validation and notification-diagnostic scripts.

### Changed
- the v1.1 `notifications_enabled` preference now controls real desktop notification delivery;
- alert classification reuses the configured `UsagePolicy` and existing LOW threshold;
- notification transport decision was revised from direct PySide6 QtDBus to `notify-send` after physical
  target validation exposed D-Bus marshalling incompatibilities in the Python binding;
- development/release checks now include the `scripts` directory where applicable;
- release metadata advances from 1.1.0 to 1.2.0.

### Compatibility and safety
- settings schema remains version 1;
- no persisted alert/deduplication state is introduced;
- stale snapshots and provider failures do not fabricate alert transitions;
- notification-delivery failure does not invalidate a successful usage refresh or stop later refreshes;
- raw provider payloads and credentials do not cross the notification boundary;
- v1.0/v1.1 provider, tray, settings and desktop contracts remain in force.

### Validation
- acceptance, unit, architecture and regression suites passed;
- repository-wide pytest, ruff, strict mypy and compileall gates passed during implementation;
- `notify-send` diagnostics returned success and a positive notification id on Ubuntu/GNOME/Wayland;
- LOW and EXHAUSTED notifications were visibly presented and distinguishable on the target workstation.

See `docs/specs/v1.2/RELEASE.md`, `docs/TRACEABILITY-REQ-ALERT-001.md`,
`docs/VALIDATION-REQ-ALERT-001.md` and `docs/adr/ADR-006-linux-notifications.md`.

## 1.1.0 — 2026-08-08

Validated settings release of CodexBar.

### Added
- persistent schema-v1 user settings under the canonical XDG configuration directory;
- configurable LOW remaining-usage threshold;
- configurable automatic refresh interval with validated range `10..3600` seconds;
- persisted `notifications_enabled` preference for future alert behavior;
- `codexbar settings show` and `codexbar settings reset`;
- Qt Settings dialog with Save, Cancel, Reset and validation feedback;
- Settings action in both the Qt tray menu and the native Ayatana helper menu;
- typed corruption/schema diagnostics and deterministic fallback to defaults.

### Changed
- runtime usage classification now consumes the persisted LOW threshold through the existing
  `UsagePolicy`;
- automatic refresh cadence can change without restarting CodexBar and retains the existing
  no-overlapping-refresh guard;
- settings writes use versioned JSON and atomic replacement semantics;
- release metadata is advanced from 1.0.0 to 1.1.0.

### Compatibility and safety
- v1.0 provider, domain, tray, desktop-installation and failure-safety contracts remain in force;
- malformed or unsupported settings documents do not prevent application startup;
- reading a corrupt settings document does not silently overwrite it;
- Snap-scoped configuration paths fall back to the canonical host-user configuration location;
- notification delivery remains deferred to `REQ-ALERT-001`.

### Validation
- `REQ-SETTINGS-001` acceptance, unit, architecture and GUI tests passed during implementation;
- repository-wide pytest, ruff, strict mypy and compileall gates passed at the implementation gate;
- the settings lifecycle was validated on the target Ubuntu/GNOME/Wayland workstation;
- target validation discovered and closed a native Ayatana menu-parity defect before release.

See `docs/specs/v1.1/RELEASE.md`, `docs/TRACEABILITY-REQ-SETTINGS-001.md` and
`docs/VALIDATION-REQ-SETTINGS-001.md`.

## 1.0.0 — 2026-08-08

First validated release of CodexBar.

### Included
- authenticated Codex usage/rate-limit retrieval through the local Codex app-server;
- normalized dynamic usage windows with stale/error semantics;
- Linux tray UI with project-owned icon, refresh/detail/quit interaction and Qt fallback;
- optional Ayatana native indicator label through an isolated system-Python helper;
- supervision, diagnostics and Snap/IDE runtime-environment sanitization for the native helper;
- canonical user-local `uv tool` installation with XDG desktop entry and icon;
- opt-in, reversible autostart;
- managed uninstall and checkout-independent installed execution;
- protection against Snap-scoped XDG installation paths;
- repository-wide pytest, ruff, strict mypy and compileall release gates.
