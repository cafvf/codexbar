# CodexBar v1.7 — Product and Architecture Decisions

Status: frozen for implementation
Theme: Diagnose

## DEC-1701 — Diagnose is a product surface

Decision: ACCEPTED

System Health is a user-facing capability, not only developer logging.

One conceptual health snapshot is rendered through CLI, JSON and UI.

## DEC-1702 — Orthogonal health dimensions

Decision: ACCEPTED

Availability, freshness, operational health and Context coverage remain separate.

Initial common enums:

- availability: `available`, `unavailable`, `unsupported`, `not_applicable`;
- operational health: `ok`, `degraded`, `failed`;
- freshness where meaningful: existing `current` / `stale`, plus `unknown` only
  in diagnostic presentation.

An overall health label is derived presentation, not source truth.

## DEC-1703 — Overall health

Decision: ACCEPTED

Overall presentation uses:

- `healthy`;
- `degraded`;
- `needs_attention`.

Rules:

- `needs_attention`: no usable Current/source path or failed instance ownership
  invariant;
- `degraded`: Current is stale or a non-critical capability has a meaningful
  operational failure;
- `healthy`: critical Current/source/runtime path is healthy and no meaningful
  degradations are active.

Context insufficient coverage alone does not degrade overall health.

Native Ayatana unavailability with healthy Qt fallback does not degrade overall
health.

## DEC-1704 — Diagnostics are read-only

Decision: ACCEPTED

Doctor/System Health may inspect and probe but never repair/mutate.

No `doctor --repair` behavior is part of v1.7.

## DEC-1705 — Runtime metrics are bounded and ephemeral

Decision: ACCEPTED

Use a bounded in-memory ring per operation with capacity 64.

For one operation family:

- show `last` when N >= 1;
- show empirical p50 when N >= 3;
- show empirical p95 only when N >= 20;
- otherwise state that evidence is insufficient for that aggregate.

Durations use a monotonic clock.

No persistence, telemetry or network export.

## DEC-1706 — Single-instance mechanism

Decision: ACCEPTED

Use `QLocalServer` / `QLocalSocket` for per-user/session GUI ownership.

Initial protocol:

- `PING`;
- `SHOW_DETAILS`.

Do not build a general remote-control API in v1.7.

A stale local endpoint must be recoverable.

## DEC-1707 — Context revision model

Decision: ACCEPTED

Use explicit monotonically increasing Current and History revisions.

Conceptual Context cache identity:

    (current_revision, history_revision, UsageWindowId)

Current revision advances when a new authoritative Current observation is adopted.

History revision advances only after an effective History mutation relevant to
read results, including successful append, clear, or prune that removes rows.

## DEC-1708 — Lean Context projection

Decision: ACCEPTED

Keep `ContextHistoryRepository`.

The schema-v1 SQLite adapter should read only the columns required to construct
`ContextObservation`.

Final cycle grouping, selection, tolerance, tie-break and empirical statistics
remain outside SQL.

## DEC-1709 — Asynchronous Context

Decision: ACCEPTED

Use the established executor + generation pattern.

A completed Context result is rendered only if its captured Current/History
revision pair remains current.

No heavy Context repository query may execute synchronously from Qt render code.

## DEC-1710 — Asynchronous redeem UI

Decision: ACCEPTED

Keep `RedeemProcessManager` semantics intact.

Introduce an orchestration/controller layer that runs external consume/refetch work
off the Qt thread and exposes UI execution state separately from durable ledger
state.

## DEC-1711 — Account lineage contract

Decision: ACCEPTED

The supported app-server surface currently does not expose a stable opaque account
ID.

v1.7 therefore:

- declares History/Context single-account local evidence;
- does not persist raw email as authoritative lineage;
- does not decode private auth/JWT storage;
- exposes the limitation in System Health;
- documents History clear as required hygiene after intentional account switch.

No History schema-v2 migration is authorized by this decision.

## DEC-1712 — Rate-limit source selection

Decision: ACCEPTED

If `rateLimitsByLimitId.codex` is present and structurally valid, use it.

Otherwise use the legacy `rateLimits` snapshot.

The existence of additional non-Codex limit IDs must not merge unrelated quota
windows into the CodexBar Current snapshot.

## DEC-1713 — Budget without reserve

Decision: ACCEPTED

No configured reserve means policy headroom is **not applicable**, not zero.

Domain and UI must represent that distinction explicitly.

## DEC-1714 — Reset fact notifications

Decision: ACCEPTED

Do not activate new reset-expiry/count-change notifications in v1.7.

Existing primitives are classified as deferred product capability for v1.9 Plan or
another explicit release.

## DEC-1715 — Native diagnostics

Decision: ACCEPTED

Drain native-helper stderr safely into a bounded recent diagnostic buffer.

The native width guide must be derived dynamically and must not encode a permanent
5h/Weekly domain assumption.

## DEC-1716 — CI matrix

Decision: ACCEPTED

Project declares Python >=3.12,<3.15, therefore headless CI covers:

- 3.12;
- 3.13;
- 3.14.

Physical Ayatana/GNOME rendering remains outside hosted CI.

## DEC-1717 — Version authority

Decision: ACCEPTED

`pyproject.toml` is the single project-version authority.

Runtime `__version__` should derive from installed package metadata after tests
confirm correct behavior under `uv run`, editable/development execution and
`uv tool install`.

No independent source-code release literal should remain.

## DEC-1718 — UI consolidation scope

Decision: ACCEPTED

Refactor tray/history/control composition only where needed by v1.7 capabilities.

A wholesale hierarchy rewrite is not a release goal.

## DEC-1719 — Persistent app-server session

Decision: EVIDENCE-GATED, DEFAULT REJECTED

Default remains one-shot.

Phase A records spawn / initialize / request / parse / shutdown timing.

A persistent supervised session requires a separate stop/go decision showing
material benefit and a safe reconnect/lifecycle design.

Failure to justify it means no implementation change.

## DEC-1720 — History maintenance / WAL

Decision: EVIDENCE-GATED, DEFAULT UNCHANGED

Characterize append/prune and concurrent read/write behavior.

Do not change prune cadence or SQLite journal mode without measured benefit and
an explicit retention/concurrency contract.

## DEC-1721 — Ayatana migration

Decision: EVIDENCE-GATED, DEFAULT UNCHANGED

Deprecation warning alone is not a migration requirement.

A replacement backend needs prototype, automated diagnostic and physical target
validation before the current helper is removed.

## DEC-1722 — Performance budgets

Decision: ACCEPTED

Release-blocking target-workstation budgets:

- Context cache-hit p95 <= 5 ms;
- synchronous Qt work caused by Context refresh/render p95 <= 50 ms;
- second-instance `SHOW_DETAILS` round trip p95 <= 250 ms;
- local-only Doctor collection p95 <= 500 ms.

Engineering target, not hard release blocker:

- cold full Context computation p95 <= 150 ms.

External source probes are timed separately and remain governed by their explicit
source timeout.

Normal shared CI must not use wall-clock performance thresholds as flaky unit-test
assertions.

## DEC-1723 — Diagnostic JSON schema

Decision: ACCEPTED

`doctor --json` emits `diagnostics_schema_version: 1`.

Fields may be added compatibly within v1.7, but existing field meanings must not
change silently.

No tokens, raw authentication payload, or raw account email are emitted by
default.
