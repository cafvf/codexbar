# Changelog

## 1.8.0 — 2026-08-14

Validated **Plan** release.

### Added
- explicit per-window Plan checkpoints keyed by opaque `UsageWindowId` and whole-second time-to-reset coordinates;
- deterministic Plan evaluation with active checkpoint resolution, effective floor, signed margin and ABOVE/AT/BELOW compliance;
- Settings schema v3 with checkpoint persistence and an explicit Plan breach-notification opt-in;
- typed Plan checkpoint editor and CLI inspection while preserving currently absent window policies;
- Current Details Plan panel derived from the same captured Current observation as existing Current surfaces;
- factual CURRENT-only Plan breach notifications with silent baselines, dedupe, recovery/rearm, policy/cycle rebaseline and delivery-failure isolation;
- Plan alert physical-validation scenarios integrated into the existing notification harness.

### Changed
- explicit Settings saves now write canonical schema 3; schema 1 and 2 remain readable without rewrite-on-load;
- Current presentation honors the configured LOW threshold while Plan remains a separate deterministic policy comparison;
- release version advances to 1.8.0 with `pyproject.toml` remaining the sole version authority;
- hosted version-mode validation uses the release-neutral `scripts/validate_release_version_modes.py` entry point.

### Compatibility and safety
- `UsageReservePolicy` remains the sole configured reserve owner and Budget remains Plan-independent;
- History, Historical Context, reset ledger and reset-credit inventory have no Plan authority;
- STALE data is not presented or notified as current Plan compliance;
- existing LOW/EXHAUSTED alert semantics remain unchanged;
- no forecast, time-to-exhaustion estimate, exhaustion probability or automatic redeem is introduced;
- refresh and authoritative post-redeem `adopt_snapshot()` converge through the same Plan evaluation/alert path;
- no Plan-specific persistence, worker, scheduler, cache or revision subsystem is introduced.

### Validation
- implementation-completion gate: 815 tests passed; Ruff, strict mypy, compileall and `git diff --check` passed;
- final post-bump release-prep gate: 819 tests passed; Ruff, strict mypy, compileall and `git diff --check` passed;
- uv-run, editable and isolated uv-tool version modes all report metadata/runtime 1.8.0;
- Settings add/edit/remove/Save/Cancel/Reset behavior physically validated on Ubuntu/GNOME/Wayland;
- PlanPanel placement, live Settings application, 30d checkpoint rendering and Budget-vs-Plan independence physically validated;
- Plan breach/rearm/disabled/activation notification scenarios passed using the existing desktop-notification harness;
- released LOW/dedupe/disabled/multi-window notification scenarios remained green;
- final native/window lifecycle release-candidate smoke passed; Qt/Wayland text-input diagnostics were non-fatal;
- release-prep CI run `31858424480` succeeded on exact commit `dd87b4716fe29c5d433704079b729338c42e33c4`;
- final tag-target CI run `31858617233` succeeded on exact commit `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`;
- annotated tag `v1.8.0` was remotely verified and points to `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`.

Final local/hosted gates and tag evidence are recorded in `docs/VALIDATION-v1.8.0.md` and `docs/RELEASE-CHECKLIST-v1.8.0.md`.

## 1.7.0 — 2026-08-14

Release candidate **Diagnose**.

### Added
- unified typed runtime diagnostics shared by Doctor, JSON diagnostics and System Health;
- `codexbar doctor` and `codexbar doctor --json` with read-only/secret-minimized diagnostics schema v1;
- bounded in-memory runtime metrics with monotonic timing and sample-count-aware p50/p95;
- one-owner GUI runtime with second-launch `SHOW_DETAILS` IPC;
- revision-aware Historical Context caching, lean schema-v1 candidate reads and stale-result rejection;
- asynchronous Context and reset-credit redeem orchestration outside the Qt interaction thread;
- separate human-readable System Health window with optional technical details;
- explicit account-lineage status for the single-account local-History assumption;
- hosted Python 3.12/3.13/3.14 CI and isolated uv-tool version validation.

### Changed
- Historical Context belongs to Usage History rather than Open Details;
- no-policy Budget headroom is `Not applicable` instead of an implied numeric zero;
- System Health auto-updates as a read-only observer; authoritative manual Refresh remains an Open Details action;
- runtime package version derives from package metadata, with `pyproject.toml` as the single release authority;
- native-helper stderr handling and label width guidance are hardened without replacing the validated Ayatana/Qt architecture.

### Evidence-gated decisions
- retain one-shot Codex app-server lifecycle;
- retain current History prune cadence;
- retain current SQLite journal behavior rather than enabling WAL;
- retain Ayatana helper plus Qt fallback;
- do not add a canberra hard dependency;
- do not add a property-based testing dependency for v1.7.

### Validation
- H1 local gate: 718 tests passed; Ruff, strict mypy, compileall and `git diff --check` passed;
- Doctor read-only proof: settings, History and reset-ledger hashes unchanged before/after;
- Context cache-hit p95 0.0047 ms, Qt-sync p95 0.0408 ms, cold p95 17.383 ms;
- second-instance `SHOW_DETAILS` IPC p95 7.853 ms;
- target physical validation passed after the System Health refresh-semantics correction was retested.

## 1.6.0 — 2026-08-10

Release candidate **Context**.

### Added
- Historical context in Open Details using independent prior authoritative cycles at a matching time-to-reset;
- exact hybrid comparison tolerance `min(0.05*h*, 2 hours)`;
- coverage-adaptive empirical range/median/quartile/rank presentation;
- explicit insufficient/unavailable Context states with history-failure isolation;
- v1.6 target validation, physical smoke, traceability and release tooling.

### Changed
- usage-history retention expands from 30 to 180 days while retaining history schema v1;
- cross-version Current/History/Control/Context composition was hardened and simplified;
- project version advances to 1.6.0.

### Compatibility and safety
- Context remains descriptive and non-predictive;
- Context does not influence alerts, Control/Budget, notifications or redeem;
- native tray glance remains usage-only;
- no History schema-v2 migration or speculative index is introduced.

### Validation
- Phase F target characterization: 17,280 snapshots / 34,560 window rows over 180 days;
- history database fixture size: 7,868,416 bytes;
- schema v1 retained after query/performance characterization;
- fault, sampling-gap, timezone and pseudoreplication gates passed;
- final Phase G evidence is recorded in `docs/VALIDATION-v1.6.0.md`.

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
