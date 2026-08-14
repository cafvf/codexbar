# CodexBar v1.8 — Scope Resolution

Status: resolved for requirements drafting  
Theme: Plan

Authoritative pre-REQ semantics: `PRODUCT.md` + `DECISIONS.md`

## Included

- explicit checkpoint policy by dynamic `UsageWindowId`;
- checkpoint coordinate expressed as time-to-reset duration;
- minimum-remaining floor per checkpoint;
- step-function active-checkpoint selection without interpolation;
- reuse of the existing canonical reserve policy;
- effective floor as the maximum applicable reserve/checkpoint floor;
- signed Plan margin;
- deterministic above/at/below Plan comparison;
- explicit distinction between no policy and unavailable checkpoint capability;
- partial degradation when factual reset time is unavailable;
- non-monotonic checkpoint policies permitted;
- unique checkpoint times per window;
- exact canonical checkpoint duration in integer seconds;
- canonical Settings persistence with backward-compatible migration;
- explanatory Plan presentation in Current Details;
- stale-aware rendering without stale-triggered side effects;
- optional factual notification on transition into below-Plan;
- preservation of existing Budget, Control, redeem and Current authority.

## Evidence-gated / optional extension

### Reset-credit expiry/count-change facts

Default outcome: **deferred / no runtime change**.

A factual reset-credit expiry/count-change notification may be reconsidered during
v1.8 only if supported upstream capability evidence is sufficient and the work can
remain clearly separate from Plan-status evaluation.

It is not required for v1.8 success.

## Deferred

- Explainable Context drill-down / "Why this context?";
- Cycle Explorer;
- expanded 90d/180d History views;
- History/reset-ledger export;
- support bundle expansion beyond v1.7;
- Activity/session inference;
- account-aware historical persistence unless separately justified;
- Plan-evaluation persistence/history;
- generic notification rule engine;
- arbitrary alert-expression DSL;
- policy feasibility analysis.

## Explicitly prohibited from v1.8 Plan semantics

- forecasting;
- predicted consumption;
- time-to-exhaustion;
- probability of exhaustion;
- future checkpoint compliance prediction;
- History as Plan input;
- Historical Context as Plan input;
- empirical bands as Plan authority;
- inferred reserve/checkpoint policy;
- automatic reserve changes;
- automatic redeem;
- fixed "5h" / "weekly" domain concepts;
- interpolation between checkpoints.

## Release-shape expectation

The next stage is requirements decomposition, expected initially around:

- deterministic Plan evaluation;
- checkpoint policy;
- settings persistence/migration;
- Current Details presentation;
- below-Plan factual notification.

These are candidate requirement families, not yet frozen REQ identifiers or
implementation tasks.
