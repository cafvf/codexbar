# CodexBar v1.7 — Diagnose Architecture

Status: frozen for implementation

## 1. Target topology

```text
                         Codex app-server
                               |
                     supported read/mutate ports
                               |
                      Account operation lane
                               |
                  +------------+-------------+
                  |                          |
             Current read                Redeem worker
                  |                          |
       Capturing/Latest observation           |
                  |                          |
        CurrentRevision ----------------------+
                  |
        +---------+----------+
        |                    |
     History               Current
   persistence             presenter
        |
   HistoryRevision
        |
        v
ContextHistoryRepository
 lean schema-v1 projection
        |
        v
 Context worker/controller
        |
  revision-safe cache
        |
        v
 ContextViewState

DiagnosticService
  |      |       |       |
  |      |       |       +-- native/settings/environment probes
  |      |       +---------- reset ledger
  |      +------------------ History/Context
  +------------------------- Current/source/runtime metrics
        |
        v
 SystemHealthSnapshot
   /        |        \
doctor    JSON      System Health UI
```

## 2. Diagnostic domain

Introduce framework-independent diagnostic types.

Candidate concepts:

- `DiagnosticAvailability`;
- `OperationalHealth`;
- `EvidenceOrigin`;
- `SubsystemHealth`;
- `RuntimeMetric`;
- `RuntimeMetricSummary`;
- `SystemHealthSnapshot`;
- `OverallHealth`.

The domain must not import Qt, SQLite, subprocess implementation details or
platform-specific GI bindings.

## 3. Diagnostic collection

Use ports/adapters for subsystem inspection.

Examples:

- current/source diagnostic provider;
- History inspector;
- reset-ledger inspector;
- Context runtime diagnostic provider;
- settings diagnostic provider;
- native indicator diagnostic provider;
- environment/version provider.

Expected failures become typed unavailable/degraded states.

Programming errors are not silently normalized into healthy diagnostics.

## 4. Offline Doctor versus live UI

Both use the same health model but may have different evidence origins.

`codexbar doctor` may create a fresh read-only offline snapshot from:

- local storage inspection;
- configuration inspection;
- environment/version inspection;
- bounded optional source probe.

System Health UI can additionally include live in-process evidence:

- recent runtime metrics;
- native helper recent stderr;
- active cache/revision information;
- latest captured Current state.

Unavailable live-only evidence is explicit when Doctor runs outside the GUI
process.

No broad diagnostics IPC protocol is required for v1.7.

## 5. Runtime metrics

Use one bounded collector per operation key or one keyed collector with fixed
per-key capacity 64.

Required properties:

- thread-safe;
- append O(1) amortized;
- monotonic durations;
- no persistence;
- snapshot copying for presentation;
- deterministic empirical percentile convention documented in tests.

Metrics must not become dependencies for operational correctness.

## 6. Single-instance ownership

Ownership is created before the full GUI runtime begins polling/mutation
capabilities.

```text
launch --gui
    |
try connect existing endpoint
    |
    +-- success -> PING / SHOW_DETAILS -> exit
    |
    +-- no live owner
           |
       recover stale endpoint if safe
           |
       listen as owner
           |
       build GuiRuntime
```

The IPC callback that focuses the window stays on the Qt event loop.

A second process must not construct a full redeem-capable runtime before ownership
is resolved.

## 7. Current revision

Current revision belongs near the latest-authoritative-observation boundary.

A revision increments only when a new authoritative Current observation is adopted.

STALE fallback derived from an older observation does not masquerade as a new
authoritative Current generation.

The exact source type may be an observation envelope or a dedicated revision
tracker, but the revision must be explicit and testable.

## 8. History revision

History revision is a runtime invalidation token, not persistent schema state.

It advances after an effective mutation:

- new eligible snapshot appended;
- clear removed observations;
- prune removed observations.

It need not advance after duplicate append or zero-row prune.

Restart resets the in-memory revision; cache also restarts empty, so no persistent
revision is required.

## 9. Context cache and controller

```text
request(window, CurrentRev, HistoryRev)
        |
        +-- cache hit -> immediate result
        |
        +-- miss
             |
          worker
             |
       lean candidate query
             |
       existing v1.6 domain
             |
       completed result
             |
   revisions still current?
       |             |
      yes            no
       |             |
    cache/render    discard
```

The cache stores application/domain results, not Qt widgets.

## 10. Lean Context persistence adapter

`SqliteContextHistoryRepository` may execute a dedicated join that retrieves only:

- observed_at;
- remaining;
- resets_at;
- window identity as needed.

It reuses existing schema-v1 tables/indexes.

No migration is planned.

## 11. Redeem controller

Add a framework-independent execution controller around the existing
`RedeemProcessManager`.

Responsibilities:

- start only when idle;
- submit redeem/retry to worker;
- expose running/result/error state;
- reject duplicate start while active;
- suppress UI adoption after controller close;
- never alter process-manager event semantics.

The account operation coordinator remains the serialization authority.

## 12. Source contract adapter

Rate-limit parsing first resolves the Codex rate-limit snapshot:

1. valid explicit `rateLimitsByLimitId["codex"]`;
2. otherwise legacy `rateLimits`.

Only then are primary/secondary/dynamic windows parsed.

Reset-credit summary remains from the account-rate-limits response at its existing
supported location.

## 13. Account lineage

Do not add account identity fields to History schema in v1.7.

Diagnostic model exposes a lineage limitation such as:

```text
lineage:
  mode: single_account_assumption
  account_namespaced: false
```

Raw email is not required in the model.

## 14. Native helper diagnostics

Drain helper stderr concurrently into a fixed-size representation.

The diagnostics path must never block helper stdout event processing.

Dynamic label guide should be built from actual windows/glance geometry rather
than fixed known labels.

## 15. CI architecture

Hosted CI is headless.

Matrix:

- 3.12;
- 3.13;
- 3.14.

Physical tests remain documented release evidence and are not faked by hosted
virtual display alone.

## 16. Performance characterization

Characterization scripts remain separate from normal flaky CI assertions.

Phase A establishes baseline.
Phase C/D/E record before/after for changed hot paths.
Phase H records final target workstation evidence.

## 17. Failure boundaries

The following failures must remain independently degradable:

- Current source;
- History;
- Context;
- reset ledger;
- native helper;
- notification delivery;
- Doctor optional probe.

A diagnostics failure must not itself take down the monitored subsystem.
