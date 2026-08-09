# Changelog

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

### Supported baseline
- Linux;
- Python `>=3.12,<3.15`;
- a locally installed and authenticated Codex;
- `uv` for the supported installation workflow.

See `docs/specs/v1.0/RELEASE.md` and `docs/VALIDATION.md` for the release contract and validation evidence.
