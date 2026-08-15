# CodexBar v1.8 — Plan

Status: frozen for implementation
Theme: Plan
Validated baseline: v1.7.0 — Diagnose

## 1. Product question

> How does Current compare with the explicit plan I configured for this usage window?

v1.8 adds a deterministic operating-plan layer over Current. It does not predict future usage.

## 2. Product truth

Current remains the only authority for current usage.

A Plan assessment compares one factual `UsageWindow` observation with explicit user policy:

- the already-existing per-window usage reserve;
- zero or more user-configured checkpoints expressed as time remaining until the authoritative reset.

Plan does not infer user intent, consumption rate, cycle duration, probability or future state.

## 3. Stable vocabulary

Existing vocabulary remains unchanged:

- **Usage window** — one independently reported quota/rate-limit window.
- **UsageWindowId** — opaque stable identity supplied by the adapter contract.
- **Remaining fraction** — normalized `Fraction` in `[0, 1]`.
- **Current** — the latest authoritative usage observation.
- **Freshness** — `CURRENT` or `STALE`.
- **Usage reserve** — existing user policy keyed by `UsageWindowId`.
- **Usable headroom** — existing Budget value `max(remaining - reserve, 0)`.

v1.8 adds:

- **TimeToReset** — non-negative factual duration `resets_at - observed_at`.
- **Plan checkpoint** — explicit user target `(time_to_reset, minimum_remaining)` for one `UsageWindowId`.
- **Active checkpoint** — the most recently crossed checkpoint in a stepwise plan.
- **Effective floor** — the strongest currently applicable explicit constraint: reserve and/or active checkpoint.
- **Plan margin** — signed `remaining - effective_floor`, represented by `FractionDelta`.
- **Plan compliance** — `ABOVE`, `AT`, or `BELOW` the effective floor.
- **Checkpoint resolution** — explicit explanation of whether checkpoint evaluation is configured/applicable/resolvable.

## 4. Core semantics

For an observed usage window:

```text
observed_time_to_reset = resets_at - observed_at
```

The wall clock at render time is not used to move an old observation through checkpoints.

Given checkpoints:

```text
72h -> minimum 55%
24h -> minimum 30%
```

the plan is stepwise:

```text
t > 72h      -> no active checkpoint
24h < t<=72h -> 55% checkpoint active
t <= 24h     -> 30% checkpoint active
```

Equality activates the checkpoint.

There is no interpolation.

The effective floor is:

```text
effective_floor = max(configured_reserve, active_checkpoint.minimum_remaining)
```

using only components that are factually available.

The signed margin is:

```text
margin = remaining - effective_floor
```

Examples:

```text
Remaining:       63%
Reserve:         15%
Active checkpoint minimum: 55%
Effective floor: 55%
Margin:          +8 percentage points
Compliance:      ABOVE
```

```text
Remaining:       12%
Reserve:         15%
Active checkpoint minimum: 10%
Effective floor: 15%
Margin:          -3 percentage points
Compliance:      BELOW
```

## 5. Partial capability

Checkpoint evaluation requires a valid authoritative `resets_at`.

If checkpoints exist but reset time is unavailable/invalid:

- checkpoint resolution is explicit;
- no checkpoint floor is fabricated;
- an existing reserve remains independently evaluable for display;
- Plan breach notifications are withheld until the configured checkpoint component is factually evaluable.

If no checkpoint is active yet:

- this is distinct from “not configured”;
- reserve remains applicable if configured;
- without a reserve there is no effective floor/compliance yet.

If no reserve and no checkpoints exist:

- Plan is `Not configured`;
- it is never reported as “On plan”.

## 6. Freshness

A STALE snapshot may retain the factual coordinates of its last valid observation, but Current Details MUST NOT present that stale assessment as current Plan compliance.

The Plan panel therefore withholds the current compliance claim while Current is STALE.

Plan alerts never advance or emit from STALE snapshots.

## 7. Notifications

v1.8 includes one fixed factual notification category:

> notify when a CURRENT window transitions into `BELOW` its evaluable explicit Plan.

This is opt-in and disabled by default on upgrade.

Two gates apply:

```text
notifications_enabled
AND
plan_breach_notifications_enabled
```

The tracker still evolves while delivery is disabled, preventing replay when notifications are re-enabled.

No generic rule language, cron/timer rule, predictive alert or automatic action is introduced.

## 8. UI intent

Current Details gains a Plan section adjacent to the existing Control/Budget section.

Plan should answer the comparison compactly without redefining Budget:

```text
Weekly
Current: 63%
Active checkpoint: 72h -> minimum 55%
Effective floor: 55% (checkpoint)
Margin: +8 pp
Status: On plan
```

When reserve determines the floor:

```text
Effective floor: 15% (reserve)
```

When both tie:

```text
Effective floor: 55% (reserve + checkpoint)
```

Budget continues to own reserve headroom and reset recommendation.

## 9. Explicit non-goals

v1.8 does not add:

- forecast or slope-based consumption;
- estimated time to exhaustion;
- probability of exhaustion;
- History- or Context-derived Plan policy;
- empirical/historical target inference;
- checkpoint interpolation;
- automatic reserve changes;
- automatic reset-credit redemption;
- Plan persistence outside AppSettings;
- Plan event store;
- Plan cache or revision;
- Plan worker/executor;
- Plan scheduler/timer;
- generic notification rule engine;
- fixed “5h” or “weekly” concepts in the domain;
- Cycle Explorer;
- Activity/session inference.

## 10. Success criterion

v1.8 succeeds if the user can configure explicit checkpoints for dynamic usage windows, see a factual Current-vs-Plan comparison, optionally receive one transition-based breach notification category, and all existing Current/History/Context/Budget/redeem/desktop contracts remain intact.
