# REQ-SETTINGS-001 — Persistent user settings

Status: validated and closed
Priority: P0
Release: v1.1
Change taxonomy: EVOLUTION

## Requirement

CodexBar SHALL allow a user to inspect, change, persist, restore, and safely recover application
settings that control the LOW usage threshold, automatic refresh interval, and future notification
enablement without requiring source-code changes.

Settings SHALL be validated before persistence, SHALL survive process restarts, and SHALL not create a
second source of truth for domain policy.

## Scope decisions

- The initial settings model contains exactly:
  - `low_remaining_threshold`, represented as a domain `Fraction`;
  - `refresh_interval_seconds`, represented as a validated duration in seconds;
  - `notifications_enabled`, represented as `bool`.
- Defaults are:
  - LOW threshold: `0.20` remaining;
  - refresh interval: `60` seconds;
  - notifications enabled: `true`.
- Valid LOW threshold domain is `0 < threshold < 1`.
- Valid refresh interval domain is `10 <= seconds <= 3600`.
- Notification persistence is in scope; notification delivery behavior is deferred to `REQ-ALERT-001`.
- Desktop autostart remains owned by the desktop-integration requirement and is not an `AppSettings`
  field.
- The first settings increment exposes read/reset diagnostics through CLI. Arbitrary `settings set`
  mutation is not required.
- Settings persistence follows `XDG_CONFIG_HOME/codexbar/settings.json`, falling back to
  `$HOME/.config/codexbar/settings.json`.
- Snap-scoped XDG config values below `$HOME/snap/` SHALL be treated consistently with the v1.0 desktop
  isolation policy and SHALL fall back to the canonical host-user config location.
- The persistence document begins with `schema_version: 1`.
- Persistence-format evolution requires an ADR and explicit compatibility behavior.

## Architecture

The dependency direction is:

`persistent settings -> AppSettings -> UsagePolicy -> UsageViewModel`

`AppSettings.low_remaining_threshold` configures `UsagePolicy.low_remaining_threshold`; it does not
replace or duplicate `UsageWindow.state()` domain semantics.

The domain SHALL NOT import JSON, pathlib, XDG, Qt, or infrastructure modules.

Application use cases SHALL depend on a settings port. Filesystem/JSON persistence is an infrastructure
adapter. Qt consumes application contracts.

## Error policy

Expected settings failures SHALL be normalized rather than leaking raw JSON/filesystem exceptions
through application/UI boundaries.

The initial error taxonomy SHALL distinguish at least:

- invalid requested setting value;
- unsupported persisted schema;
- malformed/corrupt persisted settings;
- settings read failure;
- settings write failure.

A malformed or unreadable persisted file SHALL NOT prevent CodexBar from starting. The effective
settings SHALL fall back deterministically to current defaults and the diagnostic state SHALL report the
problem. The corrupt file SHALL NOT be silently overwritten merely by reading settings.

An unsupported future `schema_version` SHALL fail closed for that persisted document: CodexBar SHALL
not guess field semantics.

## Persistence contract

Canonical schema v1:

```json
{
  "schema_version": 1,
  "low_remaining_threshold": "0.20",
  "refresh_interval_seconds": 60,
  "notifications_enabled": true
}
```

The threshold is serialized as a decimal string so the persistence contract does not introduce binary
floating-point ambiguity.

Writes SHALL be atomic from the reader's perspective: write a sibling temporary file, flush/close it,
then replace the managed settings file. A failed write SHALL leave the previous valid settings document
intact whenever the underlying filesystem provides atomic replace semantics.

Unknown additional fields in schema v1 SHALL be rejected rather than silently becoming product
behavior.

## Use cases and acceptance criteria

### UC-SETTINGS-001 — Load effective settings

- AC-SETTINGS-001: when no settings file exists, loading returns exactly the documented defaults and
  does not require creating a file.
- AC-SETTINGS-002: a valid schema-v1 settings document is loaded with no loss of value or unit.
- AC-SETTINGS-003: a process restart followed by loading returns the values previously persisted.
- AC-SETTINGS-004: `XDG_CONFIG_HOME` selects the settings location; a Snap-scoped value below
  `$HOME/snap/` falls back to `$HOME/.config`.
- AC-SETTINGS-005: malformed JSON, invalid persisted values, and unsupported schema versions do not
  crash application startup; defaults become effective and a typed diagnostic is available.
- AC-SETTINGS-006: merely loading a corrupt document does not overwrite or delete that document.

### UC-SETTINGS-002 — Save settings

- AC-SETTINGS-007: saving valid settings persists the complete schema-v1 document.
- AC-SETTINGS-008: LOW thresholds outside `0 < threshold < 1` are rejected before persistence.
- AC-SETTINGS-009: refresh intervals outside `10..3600` seconds are rejected before persistence.
- AC-SETTINGS-010: non-boolean notification values are rejected at the persistence/input boundary.
- AC-SETTINGS-011: a failed write does not expose a partially written settings document as the managed
  file.

### UC-SETTINGS-003 — Apply settings to runtime behavior

- AC-SETTINGS-012: the configured LOW threshold is converted into `UsagePolicy` and changes window
  classification without changing provider data.
- AC-SETTINGS-013: changing the refresh interval updates future automatic refresh scheduling without
  requiring process restart and without creating overlapping refreshes.
- AC-SETTINGS-014: `notifications_enabled` is available to application/UI state but does not itself
  trigger notification behavior in this requirement.

### UC-SETTINGS-004 — Reset settings

- AC-SETTINGS-015: explicit reset restores exactly the current documented defaults.
- AC-SETTINGS-016: reset is idempotent.
- AC-SETTINGS-017: reset does not remove unrelated files from the CodexBar configuration directory.

### UC-SETTINGS-005 — Inspect settings

- AC-SETTINGS-018: `codexbar settings show` reports the effective values and whether defaults or a
  persisted document supplied them.
- AC-SETTINGS-019: `codexbar settings reset` invokes the same reset behavior used by the application
  layer and reports success/failure without requiring the GUI.

### UC-SETTINGS-006 — Edit settings in the GUI

- AC-SETTINGS-020: the settings surface opens with the current effective values.
- AC-SETTINGS-021: Save validates and persists the edited values, then applies runtime-relevant changes.
- AC-SETTINGS-022: Cancel closes without changing persisted or effective settings.
- AC-SETTINGS-023: Reset restores the documented defaults through the same application use case used by
  the CLI.
- AC-SETTINGS-024: validation failures are shown without closing the settings surface or persisting a
  partial update.

## Architectural invariants

- INV-SETTINGS-001: domain settings types import no UI or infrastructure module.
- INV-SETTINGS-002: JSON/XDG/path handling exists only at the infrastructure/desktop boundary.
- INV-SETTINGS-003: `UsagePolicy` remains the only domain policy used by `UsageWindow.state()`.
- INV-SETTINGS-004: notification delivery is not implemented as a side effect of settings persistence.

## Validation disposition

REQ-SETTINGS-001 is validated and closed.

Evidence:
1. acceptance and unit suites passed on the target checkout;
2. the v1.0 regression suite remained green;
3. repository-wide `pytest`, `ruff`, `mypy`, and `compileall` gates passed;
4. ADR-005 is accepted and governs persistence/schema compatibility;
5. the target Ubuntu/GNOME/Wayland workstation validated open/edit/save/cancel/reset, invalid-input
   feedback, live refresh-interval application, LOW-threshold runtime application, native Ayatana
   Settings-menu integration, and persistence across process restart.

The accepted refresh-interval domain is inclusive `10..3600` seconds. Values such as 3500 are valid;
3601 is invalid.
