# Changelog

## 1.4.0 — 2026-08-10

Validated **Understand** release of CodexBar.

### Added
- read-only descriptive analytics over v1.3 schema-v1 historical observations;
- 24h/7d/30d analytical periods with one captured end instant and half-open interval semantics;
- historical summaries for count, first/latest, observed min/max and observed change;
- historical observation chart positioned by actual observation timestamps with an explicit period time axis;
- richer CURRENT cards with visual remaining indicator, AVAILABLE/LOW/EXHAUSTED state, freshness/age and reset presentation;
- stable CURRENT -> History navigation through `UsageWindowId`;
- dedicated v1.4 target-validation script and release traceability records;
- GUI lifecycle stabilization requirement and regression suite.

### Changed
- History exposes Period as its only visible filter in v1.4; focused window identity is retained internally;
- a focused identity with no samples now remains that identity and produces EMPTY instead of silently selecting another window;
- CURRENT details are composed once and rendered on state transitions rather than rebuilt on every poll tick;
- History is a top-level sibling surface with independent show/hide polling lifecycle;
- missing reset metadata may be shown explicitly as `Reset: not reported`;
- release metadata advances to 1.4.0.

### Compatibility and safety
- history schema remains 1; settings schema remains 1;
- 30-day retention and CURRENT-only history capture remain unchanged;
- whole-percent CURRENT presentation remains compatible;
- analytics and charts do not interpolate, forecast, estimate token use or reconstruct unobserved states;
- alerts and settings policy remain independent of historical reads;
- native-helper isolation and Qt fallback contract remain intact.

### Validation
- final target gate: **353 tests passed**;
- Ruff, strict mypy and compileall passed;
- `history inspect` remained `ready_non_empty`, schema 1;
- native indicator diagnostic API path passed;
- mandatory physical checks passed on Ubuntu/GNOME/Wayland, including CURRENT -> History, History period switching and CURRENT refresh with History hidden/visible;
- Qt fallback physical re-run was conditionally skipped while automated compatibility remained covered.

### Deferred maintenance
- Ayatana deprecation warning tracked as `FUTURE-001`;
- `canberra-gtk-module` warning tracked as `FUTURE-002`.

See `docs/specs/v1.4/RELEASE.md`, `docs/TRACEABILITY-v1.4.md`, `docs/VALIDATION-v1.4.0.md` and `docs/RELEASE-CHECKLIST-v1.4.0.md`.

## 1.3.0 — 2026-08-09

Validated **Remember** release: schema-v1 SQLite history for normalized CURRENT observations, fixed 30-day retention, history inspect/clear, failure isolation and discrete-observation semantics.

Earlier release records remain authoritative in their release-specific documentation.
