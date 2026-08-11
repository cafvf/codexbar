# CodexBar Product Roadmap

Status: active planning roadmap
Current release: v1.6.0 — Context
Last reviewed: 2026-08-10

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
| v1.7 | Diagnose | Is CodexBar healthy, coherent, responsive, and explainable? | Planning |
| v1.8 | Explore | Why did Context choose this evidence and how do cycles compare? | Proposed |
| v1.9 | Plan | How does Current compare with explicit user-defined checkpoints? | Proposed |
| v2.0 | Activity | How does observed Codex activity organize into sessions/work patterns? | Research horizon |

## Roadmap principles

1. Current remains authoritative.
2. History remains observational evidence.
3. Context remains descriptive unless a future release explicitly introduces a
   separately named predictive capability.
4. Control remains deterministic and must not inherit authority from Context.
5. Destructive reset-credit operations remain explicit, manual, durable, and
   idempotent.
6. New persistence schemas require measured justification and a migration plan.
7. Desktop responsiveness is a product requirement, not merely an implementation
   detail.
8. A feature that cannot explain its source, freshness, or capability state should
   not silently pretend to be available.
9. Cross-account and cross-window data lineage must be explicit before analytics
   become more sophisticated.
10. Physical Linux desktop validation remains necessary for native integration.

## v1.7 — Diagnose

Primary intent:

> Make CodexBar able to explain its own operational state while consolidating the
> runtime foundations required for richer future analytics.

v1.7 is intentionally both a user-visible and engineering release. It should
improve reliability, responsiveness, diagnosability, and architectural clarity
without adding forecasting.

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

## v1.8 — Explore

Proposed product direction:

- Explainable Context / “Why this context?”;
- show selected comparable cycles and exclusion reasons;
- expose time-to-reset mismatch for each selected cycle;
- Cycle Explorer in time-to-reset coordinates;
- History 90d/180d views with visual downsampling only;
- CSV/JSON export for History and reset ledger;
- support bundle with sanitized diagnostics.

v1.8 should remain descriptive. It must not turn empirical bands into confidence or
prediction intervals.

## v1.9 — Plan

Proposed product direction:

- user-defined time/checkpoint floors by UsageWindowId;
- deterministic plan status relative to those checkpoints;
- richer reserve policies;
- configurable factual notification rules;
- formal runtime integration of reset-credit expiry/count-change facts if capability
  evidence supports it.

The intended framing is “plan versus current fact,” not predicted consumption.

## v2.0 — Activity research horizon

Possible major-version direction:

- account-aware persistence / profiles;
- observed activity sessions derived from discrete quota changes;
- temporal work-pattern summaries;
- optional project/repository attribution only if a reliable local data source exists;
- possible History schema evolution;
- persistent supervised Codex app-server session only if characterization justifies it.

A v2.0 proposal requires a separate product/specification review and is not implied
by this roadmap.

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
