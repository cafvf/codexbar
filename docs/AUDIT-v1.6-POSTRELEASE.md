# CodexBar v1.6.0 — Post-release Product and Architecture Audit

Status: planning input
Audited baseline: v1.6.0 — Context
Audit date: 2026-08-10

## 1. Executive assessment

CodexBar has evolved from a small tray monitor into a local desktop application
containing several deliberately separate authorities:

- Current usage;
- local observational History;
- empirical Historical context;
- deterministic Control/Budget;
- reset-credit current state;
- durable reset event ledger;
- explicit idempotent redeem processing;
- native/Qt desktop integration.

The dominant risk for future releases is no longer missing functionality. It is
growing coupling between otherwise well-designed subsystems at composition and UI
boundaries.

The domain model and safety boundaries should be preserved. Future work should
focus on runtime consolidation, data lineage, responsiveness, diagnostics, and
evidence-driven optimization.

## 2. Strengths to preserve

### 2.1 Explicit data authority

Current remains authoritative; History and Context do not replace missing Current.
Control does not inherit authority from Context.

### 2.2 Strong domain types

Fractions, window identities, freshness, Context coverage, reset-credit identities,
and event states are explicit and strongly validated.

### 2.3 Durable destructive-operation semantics

Redeem is explicit, confirmation-gated, serialized, durably begun before external
mutation, idempotent on retry, and capable of representing unknown outcomes.

### 2.4 Failure isolation

History/Context/reset-ledger failures can be withheld independently without
silently corrupting Current.

### 2.5 High-value regression discipline

The repository uses unit, integration, architecture, characterization, fault
injection, target-machine validation, and physical desktop smoke checks.

## 3. Architecture findings

### AUD-001 — Version-stratified UI runtime

Current UI composition retains three historical shell generations:

- base tray;
- History tray;
- Control tray.

This protected previous releases well, but it now encodes product history in the
runtime architecture.

Direction:

- converge toward one desktop shell consuming explicit capabilities/read models;
- preserve old acceptance contracts as tests, not as separate runtime generations;
- remove direct extension through private implementation state.

Priority: P1.

### AUD-002 — Details surfaces are composed independently

Current/Reset/Budget/Redeem and Context are presented through separate presenters
and render paths.

Direction:

- consider a coherent `DetailsViewState` / details read-model composition;
- preserve subsystem authority while presenting one observation generation.

Priority: P2 after v1.7 runtime work.

### AUD-003 — Account data lineage is not explicit

History and Context are keyed by source/window/time but not by stable account
identity.

Risk:

- if the authenticated Codex account changes, observations from different accounts
  may share the same local store.

Direction:

- characterize whether the supported source exposes a stable non-secret account
  identity;
- define a single-account assumption or account-aware namespace;
- do not introduce a History schema migration without a reviewed lineage design.

Priority: P0 investigation for v1.7.

### AUD-004 — Window identity assumes duration uniqueness

Current canonical IDs use `window_<duration>m`.

Direction:

- document the assumption that duration uniquely identifies a supported quota
  window;
- add contract characterization for future source changes;
- avoid changing existing identity semantics without migration analysis.

Priority: P2.

## 4. Performance and responsiveness findings

### AUD-101 — Context end-to-end cost exceeds SQL cost

v1.6 target characterization:

- Context candidate SQL p95: ~27 ms;
- production Context p95: ~201 ms.

This indicates materialization/application selection dominates SQLite query cost.

Direction:

- benchmark a dedicated schema-v1 Context projection that constructs only
  `ContextObservation`;
- keep final selection/tolerance/tie-break semantics in the domain;
- do not introduce schema v2 or speculative indexes.

Priority: P1.

### AUD-102 — Context recomputation can be redundant

Context is rendered from the latest captured observation and can be recomputed on
UI state transitions even if the observation did not change.

Direction:

- memoize by authoritative observation identity/generation;
- invalidate on new Current observation or History mutation relevant to the query;
- record cache hit/miss and Context latency in diagnostics.

Priority: P1.

### AUD-103 — Context is synchronous at the presentation boundary

History and Current refresh already use worker/controller generation patterns.
Context does not.

Direction:

- introduce a framework-independent Context controller using the established
  executor + generation pattern;
- keep Qt rendering on the UI thread.

Priority: P1.

### AUD-104 — Redeem network/process I/O runs synchronously from Qt action

Redeem process semantics are strong, but the UI calls them synchronously.

Direction:

- preserve the process manager unchanged semantically;
- execute consume/refetch in a worker;
- expose explicit in-progress/completed/failed/recovery states;
- preserve account-operation serialization.

Priority: P1.

### AUD-105 — App-server process/handshake cost is uncharacterized

Each operation currently creates an app-server transport, initializes it, performs
one request, then closes it.

Direction:

- measure spawn, initialize, request, parse, and shutdown separately;
- only propose a persistent supervised session if measurements justify the added
  lifecycle complexity.

Priority: P1 characterization; implementation evidence-gated.

### AUD-106 — History prunes on every CURRENT capture

History performs append and prune for every accepted CURRENT observation.

Direction:

- characterize transaction/lock cost;
- consider bounded maintenance cadence or transactional append+prune;
- keep the 180-day retention contract precise.

Priority: P2.

### AUD-107 — Full History query has N+1 behavior

The generic full-snapshot query fetches windows per snapshot.

Direction:

- optimize before using that path for large exports/diagnostics;
- no urgency if current UI hot paths do not use it.

Priority: P3.

### AUD-108 — SQLite WAL has not been characterized

Multiple read/write workers may eventually justify WAL.

Direction:

- benchmark concurrent refresh/History/Context behavior before changing journal
  mode.

Priority: evidence-gated.

## 5. Runtime and operational findings

### AUD-201 — No explicit single-instance product contract

Multiple GUI processes could each own polling, notifications, persistence, native
indicator state, and an in-process account-operation coordinator.

Direction:

- establish a single-instance contract;
- preferred UX: second invocation signals the existing instance to show details;
- fail safely if IPC is unavailable.

Priority: P0/P1 for v1.7.

### AUD-202 — Native helper stderr is not a first-class diagnostic stream

Direction:

- bounded stderr draining/ring buffer;
- expose recent helper diagnostics in `doctor`;
- never allow diagnostic logging to grow unbounded.

Priority: P1.

### AUD-203 — Native width guide retains 5h/Weekly assumptions

Displayed glance text is dynamic, but helper width guidance is still based on the
historic 5h + Weekly form.

Direction:

- make width guidance dynamic or independent from fixed window IDs.

Priority: P2.

### AUD-204 — Ayatana deprecation remains open

This incorporates FUTURE-001.

Direction:

- evaluate supported Ubuntu/Debian GI path;
- preserve helper isolation, environment sanitization, lifecycle supervision, and
  Qt fallback;
- require physical validation before backend replacement.

Priority: P1 investigation.

### AUD-205 — canberra GTK warning remains unclassified

This incorporates FUTURE-002.

Direction:

- determine whether cosmetic;
- document optional distro guidance if useful;
- do not add a hard dependency unless behavior requires it.

Priority: P3.

## 6. Product/UX findings

### AUD-301 — Budget “no policy” semantics are visually ambiguous

Current representation can display zero headroom while also stating no reserve
policy.

Direction:

- choose and document one semantic model:
  - headroom not applicable without policy; or
  - absent reserve means explicit zero reserve.
- align domain and UI.

Priority: P1.

### AUD-302 — Reset expiry/count-change capability appears incompletely composed

Reset fact detection and notification formatting exist, but runtime ownership and
delivery need explicit review.

Direction:

- either compose the factual monitor formally, with policy/settings/tests;
- or mark it as deferred primitive and prevent documentation from implying it is
  active.

Priority: P1 audit/decision.

### AUD-303 — Diagnostics are fragmented

Existing commands cover desktop, settings, History, reset ledger, and native
indicator separately.

Direction:

- create `codexbar doctor`;
- add a System Health surface to Open Details;
- support machine-readable JSON output.

Priority: P0 product feature for v1.7.

## 7. Testing, CI, and release engineering findings

### AUD-401 — Strong local gate, weak remote enforcement

The v1.6 release was validated rigorously locally, but the release commit had no
remote status checks.

Direction:

- GitHub Actions for supported Python versions and headless gates;
- retain physical desktop validation as an additional release gate.

Priority: P0/P1.

### AUD-402 — Context is suitable for property-based testing

Direction:

- evaluate property-based tests for timezones, tolerance boundaries, cycle
  deduplication, tie-breaks, rank, and empirical quantiles;
- add a new dependency only if maintenance cost is justified.

Priority: P2.

### AUD-403 — Release metadata has multiple authorities

The v1.6 release exposed `pyproject.toml` versus package `__version__` drift.

Direction:

- choose one version authority;
- derive package/runtime version from it where practical.

Priority: P1.

### AUD-404 — Release scripts are version-specific

Direction:

- replace accumulating `validate_vX_Y.py` and metadata applicators with a generic
  release tool while preserving versioned evidence documents.

Priority: P2.

## 8. Product opportunities beyond v1.7

### Explore

- Explainable Context;
- selected-cycle evidence;
- inclusion/exclusion reasons;
- Cycle Explorer by time-to-reset;
- longer History views with chart-only decimation;
- CSV/JSON export;
- sanitized support bundle.

### Plan

- explicit user-defined checkpoints;
- deterministic plan-versus-current status;
- richer reserve policies;
- configurable factual notifications.

### Activity

- observed activity-session derivation;
- work-pattern summaries;
- account-aware/profile-aware storage;
- optional project attribution if a reliable local source exists.

## 9. Anti-goals arising from the audit

Do not use this audit as justification for:

- a broad rewrite;
- automatic schema-v2 migration;
- moving Context semantics into SQL;
- replacing executors with asyncio without a concrete problem;
- introducing prediction under the Context name;
- automatic redeem;
- persistent app-server lifecycle without measured benefit.

## 10. Recommended next action

Use this audit as planning input for v1.7 — Diagnose.

The v1.7 planning phase should convert approved findings into:

1. product requirements;
2. architecture decisions;
3. acceptance criteria;
4. performance budgets;
5. task phases;
6. a traceability matrix.

No v1.7 implementation should start until those artifacts are reviewed and frozen.
