# CodexBar v1.7 — Diagnose

Status: frozen for implementation
Theme: Diagnose
Validated baseline: v1.6.0 — Context

## 1. Product intent

CodexBar v1.7 makes the application able to explain its own operational state
while removing avoidable blocking work from interactive desktop paths.

The release should answer:

> Is CodexBar healthy, which capability is degraded when something is wrong, and
> can the application explain that fact without compromising Current or manual
> reset safety?

v1.7 is both a product and engineering release. Diagnostics are user-facing;
runtime consolidation exists to support reliability and future v1.8 exploration.

## 2. Four product pillars

### Diagnose

Expose one framework-independent System Health model through:

- `codexbar doctor`;
- `codexbar doctor --json`;
- a read-only System Health surface in Open Details.

### Isolate

Guarantee one active GUI owner per user/session. Re-launching the GUI while it is
already running should focus the existing Open Details surface instead of creating
a competing runtime.

### Do not block

Context computation and external reset-credit consume/refetch work must not perform
avoidable expensive work on the Qt interaction thread.

### Verify

The headless regression contract must execute in hosted CI for every supported
Python minor. Native desktop behavior remains additionally validated on the target
Ubuntu/GNOME/Wayland environment.

## 3. System Health

System Health is descriptive operational evidence.

It should be able to represent at least:

- Codex source availability;
- Current availability/freshness/age;
- History state/schema/bounds;
- Context availability/coverage/recent computation evidence;
- reset-ledger availability and unresolved redeem attempts;
- native-indicator backend/fallback/health;
- settings origin/schema;
- application/runtime version and environment;
- bounded recent runtime metrics and helper diagnostics.

Health dimensions are orthogonal. For example:

- Context with zero comparable cycles may be operationally healthy but have
  insufficient contextual evidence;
- native Ayatana may be unavailable while the Qt fallback keeps the application
  healthy;
- STALE Current is a freshness condition and may degrade overall status without
  fabricating an error in History.

## 4. Doctor behavior

`codexbar doctor` is read-only.

It may perform safe local inspection and bounded read-only source probes. It must
not:

- modify settings;
- clear History;
- repair databases;
- redeem reset credits;
- alter Codex authentication;
- print authentication tokens or private auth payloads.

`doctor --json` renders the same conceptual snapshot using a versioned diagnostic
schema.

## 5. Runtime metrics

v1.7 may retain bounded in-memory performance/outcome measurements.

These measurements are local diagnostics, not telemetry.

Metrics must use monotonic duration measurement and must not be persisted or
transmitted.

## 6. Context runtime

v1.6 Context semantics are frozen and remain authoritative.

v1.7 may improve only execution by:

- revision-aware memoization;
- lean schema-v1 candidate projection;
- background worker/controller orchestration;
- stale-result rejection;
- diagnostic latency/cache evidence.

No richer Context statistic is required.

## 7. Redeem runtime

v1.5/v1.6 redeem semantics remain authoritative:

- explicit user confirmation;
- durable begin before external consume;
- serialized account operation;
- idempotent retry;
- explicit unknown outcome;
- authoritative refetch after success;
- no automatic redeem.

v1.7 changes only the UI execution path so external work does not freeze Qt.

## 8. Account lineage

The supported app-server account surface does not currently expose a stable opaque
account ID suitable for durable History namespacing.

Therefore v1.7 adopts an explicit **single-account local-history assumption**:

- History is not claimed to be account-aware;
- CodexBar does not parse private token/JWT/auth storage to invent account identity;
- System Health explains the limitation;
- documentation instructs the user to clear local History after intentionally
  switching ChatGPT accounts before treating Context as comparable evidence.

A future stable supported account identifier may justify account-aware persistence
in a later release.

## 9. Source compatibility

The current upstream app-server supports a multi-bucket rate-limit response in
addition to the historical single-bucket view.

CodexBar v1.7 must preserve backward compatibility while correctly selecting the
explicit Codex rate-limit bucket when available.

This is source-contract hardening, not a new analytics feature.

## 10. Performance intent

The most important v1.7 performance requirement is bounded **UI blocking time**,
not merely total background computation latency.

A Context calculation may take longer in a worker without degrading UX as long as
the Qt thread remains responsive and stale results are rejected.

## 11. UI intent

System Health is a separate read-only section/surface.

It must not turn:

- History into Current;
- Context into alert authority;
- diagnostic severity into reset advice;
- diagnostics into automatic repair.

Existing Open Details Current/History/Context/Control/Reset conceptual separation
remains intact.

## 12. Explicitly out of scope

v1.7 does not add:

- forecasting;
- time-to-exhaustion;
- probability of exhaustion;
- automatic redemption;
- Context-driven alerts;
- Cycle Explorer;
- selected-cycle Context drill-down;
- user plan checkpoints;
- activity/session attribution;
- cloud telemetry;
- persistent diagnostics storage;
- broad UI rewrite;
- speculative History schema migration.

## 13. Success criterion

v1.7 succeeds when:

- a user can inspect major subsystem health from one CLI command and one UI
  surface;
- duplicate GUI launch does not create a competing runtime;
- repeated Context renders avoid redundant heavy computation;
- Context and redeem external work do not block the Qt interaction path;
- v1.6 Context results remain semantically identical;
- the account-lineage limitation is explicit rather than hidden;
- current app-server rate-limit shapes are handled safely;
- the supported Python range is exercised by hosted CI;
- physical Linux desktop behavior remains green.
