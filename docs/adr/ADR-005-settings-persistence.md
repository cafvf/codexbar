# ADR-005 — Settings persistence and compatibility boundary

Status: accepted for REQ-SETTINGS-001 implementation
Date: 2026-08-08

## Context

REQ-SETTINGS-001 introduces the first persistent application configuration owned by CodexBar. The
engineering constitution requires persistence formats and lasting compatibility decisions to be recorded
in an ADR before production persistence is considered complete.

The settings model must configure existing domain policy without moving filesystem, JSON, XDG or Qt
concerns into the domain.

## Decision

1. The domain owns immutable, validated settings values:
   - `AppSettings`;
   - `RefreshIntervalSeconds`.
2. `low_remaining_threshold` reuses the existing `Fraction` value object and is additionally constrained
   to the open interval `(0, 1)` by `AppSettings`.
3. `AppSettings.usage_policy()` is the only bridge from persisted/user configuration to the existing
   `UsagePolicy`; `UsageWindow.state()` remains unchanged.
4. Infrastructure will persist schema version 1 as JSON under the XDG configuration directory.
5. Decimal thresholds are serialized as decimal strings rather than JSON floating-point numbers.
6. Persisted documents are treated as an external/volatile boundary:
   - exact schema version is required;
   - unknown fields are rejected;
   - malformed or unsupported documents produce typed diagnostics and effective defaults;
   - reading a bad document does not silently rewrite it.
7. Writes use sibling temporary-file plus atomic replace semantics where supported by the host filesystem.
8. Snap-scoped XDG configuration paths below `$HOME/snap/` are rejected in favor of the canonical
   `$HOME/.config` path, matching the v1.0 host-user isolation decision.
9. Schema migrations are not guessed. A future schema version requires an explicit migration/compatibility
   decision and tests.

## Consequences

- Domain tests can validate settings semantics without filesystem or GUI dependencies.
- Persistence can evolve behind an application port without changing `UsagePolicy` or provider contracts.
- Corruption recovery favors availability while preserving evidence for diagnosis.
- The initial implementation carries a small explicit schema/versioning cost in exchange for predictable
  future evolution.

## Rejected alternatives

### Persist floating-point threshold values
Rejected because it introduces unnecessary binary floating-point representation ambiguity for a value
already represented exactly as `Decimal`/`Fraction`.

### Put LOW classification directly in AppSettings
Rejected because it would duplicate `UsagePolicy` and create two sources of truth for usage state.

### Store settings beside the source checkout
Rejected because installed CodexBar is explicitly independent of the checkout.

### Silently accept unknown fields/schema versions
Rejected because it turns misspellings or future semantics into undocumented behavior.
