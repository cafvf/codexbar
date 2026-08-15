# CodexBar Product Roadmap

Status: active planning roadmap
Current validated release: v1.7.0 — Diagnose
Release candidate: v1.8.0 — Plan
Last reviewed: 2026-08-14

## Product progression

| Release | Theme | Product question | Status |
|---|---|---|---|
| v1.0 | Observe | What Codex usage is current? | Released |
| v1.1 | Configure | How should CodexBar behave locally? | Released |
| v1.2 | Notify | When does usage cross a factual threshold? | Released |
| v1.3 | Remember | What observations were retained? | Released |
| v1.4 | Understand | What does retained history show descriptively? | Released |
| v1.5 | Control | What deterministic reserve/reset actions are available? | Released |
| v1.6 | Context | How does Current compare with independent prior cycles? | Released |
| v1.7 | Diagnose | Is CodexBar healthy, coherent, responsive, and explainable? | Released |
| v1.8 | Plan | How does Current compare with explicit user-defined checkpoints and reserves? | Release preparation |
| v1.9 | Explore | Why did Context choose this evidence and how do cycles compare? | Proposed |
| v2.0 | Activity | How does observed Codex activity organize into sessions/work patterns? | Research horizon |

## Roadmap principles

1. Current remains authoritative.
2. History remains observational evidence.
3. Context remains descriptive unless a future release explicitly introduces a separately named predictive capability.
4. Control remains deterministic and must not inherit authority from Context.
5. Destructive reset-credit operations remain explicit, manual, durable, and idempotent.
6. New persistence schemas require measured justification and a migration plan.
7. Desktop responsiveness is a product requirement, not merely an implementation detail.
8. A feature that cannot explain its source, freshness, or capability state should not silently pretend to be available.
9. Cross-account and cross-window data lineage must be explicit before analytics become more sophisticated.
10. Physical Linux desktop validation remains necessary for native integration.

## v1.7 — Diagnose

Status: released as `v1.7.0` on 2026-08-14.

Primary intent:

> Make CodexBar able to explain its own operational state while consolidating the runtime foundations required for richer future analytics.

v1.7 is intentionally both a user-visible and engineering release. It improves reliability, responsiveness, diagnosability, and architectural clarity without adding forecasting.

Primary outcomes:

- consolidated `codexbar doctor` / System Health diagnostics;
- explicit single-instance behavior;
- non-blocking heavy Context and redeem I/O;
- lower redundant Context computation;
- evidence-driven Context read optimization without schema migration;
- account/data-lineage investigation and policy;
- stronger CI/release automation;
- native-indicator maintenance and diagnostics;
- cleanup of ambiguous Budget and reset-monitor composition behavior.

See `docs/specs/v1.7/PLANNING.md`.

## v1.8 — Plan

Status: implementation complete; release preparation for `v1.8.0`.

Primary intent:

> Let the user define explicit factual operating targets for each dynamic usage window and compare Current against those targets without forecasting.

Product question:

> How does Current compare with the plan I explicitly configured for this window?

Implemented v1.8 direction:

- explicit checkpoint policy by opaque `UsageWindowId`;
- checkpoint floors expressed as whole-second time-to-reset coordinates plus minimum remaining fraction;
- existing `usage_reserves` remains the sole reserve authority;
- deterministic effective floor and signed Plan margin from Current + explicit policy;
- one optional factual notification category for transition into `BELOW`;
- Settings schema v3 with v1/v2 read compatibility and no rewrite-on-load;
- Current Details Plan panel sourced from the already captured Current observation;
- live Settings application without restart;
- one CURRENT-only in-memory breach tracker integrated into the existing refresh/adopt path;
- clear distinction between reserve, checkpoint and notification semantics;
- no reset-credit fact monitoring is required by the core v1.8 Plan scope.

Conceptual policy model:

- existing `usage_reserves`: how much capacity the user intends to preserve;
- `usage_plan_checkpoints[]`: explicit `time_to_reset_seconds + minimum_remaining` targets;
- `plan_breach_notifications_enabled`: fixed factual below-plan notification opt-in.

Architectural boundaries:

- Current remains the only authority for current usage state;
- Settings/Plan Policy define user intent;
- History and Historical Context do not influence deterministic Plan evaluation;
- Plan status does not estimate future consumption or probability of exhaustion;
- Plan status does not trigger automatic reset-credit redemption;
- Budget remains Plan-independent and continues to use the existing reserve owner;
- reset-credit notifications remain evidence-gated and factual.

Example framing:

- `Current remaining: 63%`;
- `Plan floor at this checkpoint: 55%`;
- `Margin: +8 percentage points`;
- `Status: On plan`.

This is a deterministic comparison between an observed fact and an explicit user policy. It is not a consumption forecast.

Release-preparation evidence is maintained in `docs/TRACEABILITY-v1.8.md`, `docs/VALIDATION-v1.8.0.md` and `docs/RELEASE-CHECKLIST-v1.8.0.md`. v1.8 becomes Released only after the final exact commit passes hosted CI and is tagged `v1.8.0`.

Dependency note:

v1.8 Plan depends primarily on capabilities already stabilized through v1.7: dynamic `UsageWindowId`, Current authority, Settings, Control/Budget, alerts, reset-credit capability representation, asynchronous runtime foundations, diagnostics and hosted release gates. It does not require the richer Historical Context exploration proposed for v1.9.

## v1.9 — Explore

Primary intent:

> Make retained historical evidence inspectable enough that the user can understand why Historical Context selected specific cycles and how those cycles compare.

Product question:

> Why did Context choose this evidence and how do the comparable cycles differ?

Proposed product direction:

- Explainable Context / “Why this context?”;
- show selected comparable cycles and exclusion reasons;
- expose time-to-reset mismatch for each selected cycle;
- Cycle Explorer in time-to-reset coordinates;
- History 90d/180d views with visual downsampling only;
- CSV/JSON export for History and reset ledger;
- support bundle with sanitized diagnostics.

Architectural boundaries:

- Explore remains descriptive;
- empirical bands remain empirical and MUST NOT be presented as confidence or prediction intervals;
- Cycle Explorer MUST NOT become a forecasting surface;
- History remains observational evidence and does not become Current authority;
- Control, Budget, Plan and alerts remain independent of Historical Context;
- exports and support bundles must preserve secret minimization and data-lineage rules established in v1.7.

Dependency note:

v1.9 Explore builds on v1.6 Historical Context and the v1.7 Context runtime, diagnostics and lineage foundations. It may consume Plan-related UI conventions introduced in v1.8, but its domain semantics do not depend on Plan.

## Sequencing decision: Plan before Explore

The roadmap originally listed Explore as v1.8 and Plan as v1.9.

After v1.7 runtime/diagnostic closure, the dependency graph was reviewed and the order was intentionally inverted:

- v1.8 is now **Plan**;
- v1.9 is now **Explore**.

Rationale:

1. Plan depends mostly on capabilities already mature in v1.7: Current, dynamic window identity, Settings, Control/Budget, alerts, reset-credit capabilities, diagnostics and asynchronous runtime foundations.
2. Plan does not require explainable cycle selection, Cycle Explorer or expanded History views.
3. Explore benefits from additional retained real History and can follow without losing semantic integrity.
4. Version numbers remain monotonic; the project will not release v1.9 before v1.8 and later “return” to an older version number.

The two releases remain architecturally adjacent rather than strictly chained:

`v1.7 Diagnose -> v1.8 Plan`
and
`v1.7 Diagnose -> v1.9 Explore`.

No dependency is introduced from Historical Context into Plan authority.

## v2.0 — Activity research horizon

Possible major-version direction:

- account-aware persistence / profiles;
- observed activity sessions derived from discrete quota changes;
- temporal work-pattern summaries;
- optional project/repository attribution only if a reliable local data source exists;
- possible History schema evolution;
- persistent supervised Codex app-server session only if characterization justifies it.

A v2.0 proposal requires a separate product/specification review and is not implied by this roadmap.

## Explicit non-roadmap commitments

The roadmap does not currently commit to:

- forecasting;
- probability of future exhaustion;
- Bayesian prediction;
- inferred authoritative token counts;
- automatic reset-credit redemption;
- cloud synchronization;
- telemetry collection.

Those require separate product decisions.
