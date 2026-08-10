# Changelog

## 1.5.0 — 2026-08-10

Release candidate **Control**.

### Added
- composed account read exposing usage and reset-credit current state from one upstream operation;
- independent append-only reset event ledger with deterministic projection and inspection;
- settings schema v2 with per-window reserves and schema-v1 migration-on-read;
- deterministic budget/headroom and reset-opportunity policy;
- durable, idempotent manual reset-credit redeem with explicit confirmation and restart recovery;
- factual expiry monitoring and transport-neutral notifications;
- reset-credit, budget and redeem surfaces in Current Details;
- deterministic mock control path and v1.5 target-validation tooling.

### Changed
- notification transport now accepts a generic `NotificationMessage` while LOW/EXHAUSTED transition semantics remain unchanged;
- GUI composition now carries current usage, reset/control presentation and redeem recovery while preserving History lifecycle;
- explicit settings saves now write schema 2; schema 1 remains readable and is not rewritten merely by loading;
- project version advances to 1.5.0.

### Compatibility and safety
- `UsageSnapshot` contains no reset-credit state;
- history SQLite remains schema 1 and CURRENT-only;
- v1.4 History analytics/lifecycle and native-indicator/Qt fallback contracts remain protected;
- no automatic redeem exists;
- ambiguous consume transport failures remain `OUTCOME_UNKNOWN`;
- real redeem validation is optional because it spends a real credit.

### Validation
See `docs/VALIDATION-v1.5.0.md`, `docs/TRACEABILITY-v1.5.md` and `docs/RELEASE-CHECKLIST-v1.5.0.md`.

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
- mandatory physical checks passed on Ubuntu/GNOME/Wayland.

### Deferred maintenance
- Ayatana deprecation warning tracked as `FUTURE-001`;
- `canberra-gtk-module` warning tracked as `FUTURE-002`.

## 1.3.0 — 2026-08-09

Validated **Remember** release: schema-v1 SQLite history for normalized CURRENT observations, fixed 30-day retention, history inspect/clear, failure isolation and discrete-observation semantics.
