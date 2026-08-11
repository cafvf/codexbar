# CodexBar v1.7 — Requirements

Status: frozen for implementation
Theme: Diagnose

## Requirement conventions

- MUST: release-blocking unless explicitly marked evidence-only.
- SHOULD: expected behavior with documented exception allowed.
- MAY: optional.
- "Qt blocking" means synchronous work on the Qt interaction/event thread.

## Diagnostics

### REQ-DIAG-001 — Unified diagnostic snapshot

CodexBar MUST define a framework-independent typed diagnostic snapshot covering
major runtime subsystems.

CLI, JSON and System Health UI MUST derive from the same conceptual model.

### REQ-DIAG-002 — Human-readable Doctor

`codexbar doctor` MUST return a readable subsystem-by-subsystem report.

Expected operational degradation SHOULD be represented as diagnostic state rather
than an unhandled traceback.

### REQ-DIAG-003 — Machine-readable Doctor

`codexbar doctor --json` MUST emit valid JSON with
`diagnostics_schema_version = 1`.

The JSON MUST distinguish unavailable evidence from healthy/empty evidence.

### REQ-DIAG-004 — Read-only safety

Doctor/System Health MUST NOT mutate settings, History, reset ledger, account
authentication, or reset credits.

### REQ-DIAG-005 — Secret minimization

Diagnostics MUST NOT emit:

- API/access/refresh tokens;
- raw auth/JWT documents;
- reset consume credentials/idempotency secrets beyond already safe attempt IDs;
- raw account email by default.

### REQ-DIAG-006 — Runtime metrics

Runtime metrics MUST be local, bounded and in-memory.

Per operation family the collector MUST retain at most 64 samples.

p50 MUST be suppressed for N < 3.
p95 MUST be suppressed for N < 20.

### REQ-DIAG-007 — Metric timing

Duration measurement MUST use a monotonic clock.

Wall-clock timestamps, when shown, MUST be timezone-aware.

## Health semantics

### REQ-HEALTH-001 — Orthogonal dimensions

Availability, freshness, operational health and Context coverage MUST NOT be
collapsed into one source enum.

### REQ-HEALTH-002 — Overall status derivation

Overall status MUST be derived as `healthy`, `degraded`, or `needs_attention`
using DEC-1703.

Context insufficient coverage alone MUST NOT degrade the application.

Qt fallback success MUST prevent native Ayatana unavailability from becoming an
overall failure.

### REQ-HEALTH-003 — Explicit evidence origin

Diagnostic values SHOULD state whether evidence is:

- live runtime evidence;
- local persisted inspection;
- a fresh read-only probe;
- unavailable.

## Single instance

### REQ-INSTANCE-001 — One GUI owner

At most one normal CodexBar GUI runtime MUST own active polling/notifications/
desktop indicator/redeem interaction per user/session.

### REQ-INSTANCE-002 — Useful second launch

A second `codexbar --gui` invocation MUST request `SHOW_DETAILS` from the existing
owner and exit without creating a second GUI runtime.

### REQ-INSTANCE-003 — Liveness

The instance coordinator MUST distinguish a live owner from a stale local endpoint.

### REQ-INSTANCE-004 — Stale recovery

A stale endpoint left by an abnormal exit MUST be recoverable without requiring
manual filesystem editing.

### REQ-INSTANCE-005 — Safe IPC failure

Ambiguous ownership MUST fail closed rather than knowingly start two competing GUI
owners.

## Context runtime

### REQ-CONTEXT-RUNTIME-001 — Current revision

Every adopted authoritative Current observation MUST have a monotonically
increasing runtime revision suitable for stale-result rejection.

### REQ-CONTEXT-RUNTIME-002 — History revision

Effective History mutations MUST advance a monotonically increasing History
revision.

A zero-effect operation SHOULD NOT advance the revision.

### REQ-CONTEXT-RUNTIME-003 — Cache identity

Context cache entries MUST be keyed by Current revision, History revision and
UsageWindowId.

### REQ-CONTEXT-RUNTIME-004 — Cache semantic transparency

Cached and uncached Context results for the same revisions/window MUST be exactly
equal at the domain/application result level.

### REQ-CONTEXT-RUNTIME-005 — Lean schema-v1 projection

Context infrastructure MUST be able to query schema-v1 History candidates without
constructing unrelated rich History presentation objects.

### REQ-CONTEXT-RUNTIME-006 — No SQL semantic migration

The database query MUST NOT become authoritative for cycle selection, tolerance,
tie-break, coverage, rank or quantiles.

### REQ-CONTEXT-RUNTIME-007 — Async orchestration

Context repository query and full summary computation MUST execute outside the Qt
interaction thread.

### REQ-CONTEXT-RUNTIME-008 — Stale result rejection

A Context computation completed for obsolete revisions MUST NOT overwrite a newer
Context state.

### REQ-CONTEXT-RUNTIME-009 — v1.6 semantic compatibility

All frozen v1.6 Context semantics and canonical vectors MUST remain green.

## Redeem runtime

### REQ-REDEEM-RUNTIME-001 — Non-blocking external work

External consume/refetch work initiated from the GUI MUST execute outside the Qt
interaction thread.

### REQ-REDEEM-RUNTIME-002 — Process-manager preservation

Async UI orchestration MUST NOT weaken:

- durable begin;
- account-operation serialization;
- idempotent retry;
- unknown-outcome representation;
- authoritative refetch;
- confirmation requirement.

### REQ-REDEEM-RUNTIME-003 — UI execution state

The UI MUST expose an explicit in-progress state and prevent duplicate button
activation while one redeem/retry execution is active.

### REQ-REDEEM-RUNTIME-004 — Result generation

A late result from an obsolete/closed UI lifecycle MUST NOT resurrect a closed
window or start another external mutation.

## Account lineage

### REQ-LINEAGE-001 — Honest single-account contract

v1.7 MUST document that History/Context are not durably namespaced by a stable
supported account identifier.

### REQ-LINEAGE-002 — Supported surfaces only

CodexBar MUST NOT decode private auth/JWT files or undocumented token claims to
create a durable account identity.

### REQ-LINEAGE-003 — Health visibility

System Health/Doctor MUST expose a factual lineage status indicating that local
History assumes one account unless a future supported identifier is available.

### REQ-LINEAGE-004 — Account-switch hygiene

Documentation MUST instruct the user to clear local History after intentionally
switching ChatGPT accounts before relying on cross-cycle Context.

## Upstream source contract

### REQ-SOURCE-001 — Multi-bucket Codex selection

When `rateLimitsByLimitId.codex` exists and is valid, it MUST be used as the Codex
rate-limit snapshot.

### REQ-SOURCE-002 — Legacy compatibility

When the explicit Codex multi-bucket snapshot is absent, the supported legacy
`rateLimits` snapshot MUST remain readable.

### REQ-SOURCE-003 — No unrelated bucket merge

Non-Codex limit IDs MUST NOT be silently merged into the CodexBar usage-window
snapshot.

### REQ-SOURCE-004 — Dynamic windows

Quota window identities remain derived dynamically from supported source metadata;
no fixed 5h/Weekly requirement may return.

### REQ-SOURCE-005 — Schema failure safety

Unsupported/malformed source shape MUST normalize to existing safe usage source/
schema errors.

## Budget

### REQ-BUDGET-001 — No-policy headroom

If no reserve is configured for a window, policy headroom MUST be represented as
not applicable rather than a numeric zero.

### REQ-BUDGET-002 — UI clarity

Open Details MUST not tell a user "Available to use: 0%" merely because no reserve
policy exists.

## Native integration

### REQ-NATIVE-001 — Bounded helper stderr

Native-helper stderr MUST be drained so a long-running helper cannot block because
its stderr pipe fills.

Only a bounded recent diagnostic representation may be retained.

### REQ-NATIVE-002 — Dynamic guide

Native label width guidance MUST not encode fixed 5h/Weekly window identities.

### REQ-NATIVE-003 — Safe fallback

Native helper failure MUST continue to activate the validated Qt fallback when
available.

## Reset-monitor ownership

### REQ-RESET-MONITOR-001 — No accidental activation

v1.7 MUST NOT activate new reset expiry/count-change notifications merely because
monitor primitives exist in source.

Production ownership/deferred status MUST be explicit and tested.

## Version and CI

### REQ-VERSION-001 — Single authority

`pyproject.toml` MUST be the release-version authority.

Runtime package version MUST derive from package metadata rather than an
independent release literal.

### REQ-VERSION-002 — Execution-mode compatibility

Version derivation MUST work under:

- `uv run`;
- editable/development test execution;
- installed `uv tool` execution.

### REQ-CI-001 — Supported Python minors

Hosted headless CI MUST exercise Python 3.12, 3.13 and 3.14 while that remains the
declared supported range.

### REQ-CI-002 — Core quality gate

CI MUST run at least:

- pytest;
- Ruff;
- strict mypy;
- compileall.

### REQ-CI-003 — Native physical gate remains separate

Hosted CI MUST NOT be treated as evidence that Ayatana physically renders under
Ubuntu/GNOME/Wayland.

## Performance

### REQ-PERF-001 — Baseline characterization

Before optimization claims are accepted, Phase A MUST record target-machine
baseline timings for:

- app-server spawn/initialize/request/parse/shutdown;
- Current full read;
- Context cold computation;
- repeated Context computation;
- local diagnostics collection;
- relevant History reads.

### REQ-PERF-002 — Context cache-hit budget

On the target workstation, Context cache-hit p95 MUST be <= 5 ms under the
release characterization fixture.

### REQ-PERF-003 — Qt Context blocking budget

Synchronous Qt-thread work attributable to Context refresh/render SHOULD remain
<= 50 ms p95 on the target workstation.

Architecture tests MUST additionally prove repository/full Context computation is
not invoked synchronously from Qt render code.

### REQ-PERF-004 — IPC focus budget

Second-instance `SHOW_DETAILS` local IPC p95 MUST be <= 250 ms on the target
workstation.

### REQ-PERF-005 — Doctor local budget

Local-only diagnostic snapshot collection p95 MUST be <= 500 ms on the target
workstation.

External app-server probe timing is recorded separately and is not hidden inside
this budget.

### REQ-PERF-006 — Cold Context engineering target

Cold full Context p95 SHOULD be <= 150 ms on the target workstation.

Missing this target alone does not block release if UI blocking, cache-hit and
semantic gates pass and the measured result is documented.

## Evidence-gated maintenance

### REQ-EVIDENCE-001 — Persistent app-server decision

Phase A MUST characterize one-shot app-server cost.

Persistent-session implementation is not authorized unless a documented stop/go
decision demonstrates material benefit and safe lifecycle/reconnect behavior.

### REQ-EVIDENCE-002 — History maintenance decision

Append/prune cost and zero-row prune frequency MUST be measured before changing
prune cadence.

### REQ-EVIDENCE-003 — SQLite journal decision

Concurrent Current write + History read + Context read MUST be characterized before
changing journal mode.

### REQ-EVIDENCE-004 — Ayatana migration decision

A native backend migration requires prototype + automated diagnostics + target
physical validation.

## Regression

### REQ-REGRESSION-001 — v1.6 compatibility

v1.7 MUST preserve validated v1.6 behavior for:

- Current;
- settings;
- usage alerts;
- History and 180-day retention;
- Historical Context semantics;
- Control/Budget except the intentional no-policy clarification;
- reset-credit state;
- reset ledger;
- manual redeem/idempotent recovery;
- native indicator / Qt fallback;
- dynamic usage windows;
- no automatic redeem;
- no forecasting.
