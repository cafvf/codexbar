# CodexBar v1.8 — Decisions and complexity ledger

Status: frozen for implementation

## DEC-1801 — Plan composes existing reserve; it does not own a second reserve

`UsageReservePolicy` remains the sole configured reserve authority.

Plan combines:

```text
existing UsageReservePolicy
+
new UsagePlanCheckpointPolicy
```

Rejected:

- `PlanPolicy.reserve_floor`;
- duplicated reserve fields;
- moving existing reserve into a new nested Plan document.

Reason: duplicate configuration would create two sources of truth and break the v1.5 Budget contract.

## DEC-1802 — Time coordinate belongs to the observation

Plan uses:

```text
TimeToReset.from_instants(
    observed_at=snapshot.observed_at,
    resets_at=window.resets_at,
)
```

It MUST NOT use render-time/current wall clock to move an old remaining value through checkpoints.

Reason: mixing stale remaining with a newer clock constructs a state that was never observed.

## DEC-1803 — Stepwise checkpoints, inclusive boundary, no interpolation

For current factual coordinate `t`, eligible checkpoints satisfy:

```text
t <= checkpoint.time_to_reset
```

The active checkpoint is the eligible checkpoint having the smallest `time_to_reset`.

Exact equality activates the checkpoint.

Rejected:

- interpolation between checkpoints;
- “next future target” scoring;
- consumption-rate extrapolation.

## DEC-1804 — Non-monotonic explicit floors are valid

The following is valid:

```text
72h -> 40%
24h -> 60%
```

CodexBar evaluates explicit intent; it does not infer feasibility.

Duplicate checkpoint times for the same `UsageWindowId` are invalid because they are ambiguous.

No warning system for non-monotonic policy is required in v1.8.

## DEC-1805 — Orthogonal result dimensions

Do not create one overloaded `PlanStatus`.

Use:

- `PlanCheckpointResolution`;
- `PlanCompliance`;
- optional `effective_floor`;
- optional signed `margin`.

Checkpoint resolutions:

- `NOT_CONFIGURED`;
- `RESET_MISSING`;
- `RESET_INVALID`;
- `NO_ACTIVE_CHECKPOINT`;
- `ACTIVE`.

Compliance values:

- `ABOVE`;
- `AT`;
- `BELOW`.

Freshness remains owned by Current and is not duplicated into Plan assessment.

## DEC-1806 — Shared neutral quantities get one owner with compatibility imports

`TimeToReset` and `FractionDelta` are neutral quantities used by more than one feature.

Introduce one neutral domain owner such as:

```text
codexbar.domain.quantities
```

Existing historical imports remain valid by importing/re-exporting the same class from:

```text
codexbar.domain.context.TimeToReset
codexbar.application.analytics.FractionDelta
```

`Fraction` remains where it is; moving it would create broad churn with no v1.8 benefit.

Complexity accepted: one small domain module.

Complexity avoided: import-path migration across existing tests/modules.

## DEC-1807 — Settings schema v3 stays flat and explicit

Schema v3 adds exactly:

```text
usage_plan_checkpoints
plan_breach_notifications_enabled
```

Existing `usage_reserves` remains unchanged.

Canonical JSON:

```json
{
  "schema_version": 3,
  "low_remaining_threshold": "0.20",
  "refresh_interval_seconds": 60,
  "notifications_enabled": true,
  "usage_reserves": {
    "window_10080m": "0.15"
  },
  "usage_plan_checkpoints": {
    "window_10080m": [
      {
        "time_to_reset_seconds": 259200,
        "minimum_remaining": "0.55"
      },
      {
        "time_to_reset_seconds": 86400,
        "minimum_remaining": "0.30"
      }
    ]
  },
  "plan_breach_notifications_enabled": false
}
```

Why integer seconds:

- Plan checkpoint configuration is constrained to whole-second `TimeToReset` values, so persistence is exact;
- explicit unit;
- no duration-string parser/DSL;
- independent of upstream `windowDurationMins`;
- UI can display friendly hours/days without changing persistence semantics.

`TimeToReset` remains a general neutral quantity and may represent finer `timedelta` precision for other
features. The whole-second restriction belongs to persisted Plan checkpoint policy, not to the shared
quantity itself.

Canonical order:

- window IDs lexicographically;
- checkpoints for one window in descending `time_to_reset_seconds`.

## DEC-1808 — Schema compatibility follows existing explicit-save behavior

Schemas 1 and 2 remain readable.

Reading legacy settings does not rewrite the file.

The next explicit Save writes canonical schema 3.

Malformed/unsupported documents continue to fall back according to the existing settings error policy.

Downgrade from a saved schema 3 file to an older CodexBar that does not support schema 3 is not promised.

A dedicated ADR records this evolution because ADR-005 requires an explicit compatibility decision for new schema versions.

## DEC-1809 — Fixed Plan breach opt-in instead of notification rule engine

Add:

```text
plan_breach_notifications_enabled: bool
```

Default:

```text
false
```

Global `notifications_enabled` remains the master delivery switch.

Rejected:

- `notification_rules[]`;
- expression DSL;
- per-rule cron/frequency;
- independent scheduler;
- generic policy engine.

Reason: v1.8 has exactly one factual notification need.

## DEC-1810 — Plan alert semantics reuse the current alert harness properties

The Plan tracker is in-memory and CURRENT-only.

Rules:

- first eligible observation is a silent baseline;
- transition into `BELOW` emits one event;
- remaining `BELOW` deduplicates;
- recovery to `ABOVE`/`AT` rearms;
- later transition to `BELOW` may emit again;
- delivery-disabled transitions still update tracker state;
- STALE does not emit or advance the tracker;
- a relevant Plan policy edit establishes a new silent baseline;
- a new factual reset cycle establishes a new silent baseline when checkpoints are configured;
- checkpoint-only `NO_ACTIVE_CHECKPOINT -> BELOW` inside the same resolved cycle may emit because the checkpoint just became applicable;
- configured checkpoints with missing/invalid reset make Plan breach alert evaluation ineligible until reset capability is factual again.

No persistence is required.

## DEC-1811 — Separate PlanAlertService; shared NotificationPort and snapshot path

Do not overload the existing LOW/EXHAUSTED `AlertService` with Plan-specific cycle/policy semantics.

Introduce one small `PlanAlertService`, but:

- it uses the existing `NotificationPort`;
- it is called by the existing tray snapshot/adoption path;
- it gets no executor, repository, cache or timer;
- it cannot invoke redeem.

This small separation pays for semantic isolation while preserving the existing usage-alert harness.

## DEC-1812 — Plan evaluation is pure and synchronous

Plan evaluation is O(number of checkpoints for a window), tiny relative to source/history I/O.

No worker/executor/cache/revision is introduced.

Rejected as unjustified:

- `PlanRuntime`;
- `PlanRepository`;
- `PlanRevision`;
- background Plan worker;
- memoization.

## DEC-1813 — Current Details adds one sibling panel

Add a `PlanPanel` next to the existing Control/Budget surface.

Do not merge the application Budget model into Plan.

To reduce visual duplication, Plan renders the source of the effective floor rather than reproducing the full Budget headroom block.

Recommended placement in the current panel order:

```text
Reset credits
Control / budget
Plan
Reset action
```

Exact Qt layout remains an implementation choice.

## DEC-1814 — GUI checkpoint editing uses typed controls, not a mini-language

The Settings UI must allow add/edit/remove checkpoint rows for current dynamic windows.

Rejected despite lower initial code volume:

```text
"72h=0.55,24h=0.30"
```

or similar free-text DSL.

Reason: a mini-language creates parsing, escaping, error-reporting and user-ambiguity costs that exceed the widget complexity.

The exact Qt control layout is non-normative.

Existing policies for currently absent windows must be preserved.

## DEC-1815 — UsageWindowId remains opaque outside adapter/presentation

Plan, Settings and Budget compare/store IDs; they never parse `window_300m`.

The existing compact-label presentation helper may continue to interpret known adapter IDs for UI labeling.

No v1.8 ID-format migration is introduced.

## DEC-1816 — History, Context and reset evidence have zero Plan authority

Plan evaluation inputs are only:

- current usage observation;
- explicit reserve policy;
- explicit checkpoint policy.

No History, Context, reset ledger, empirical band, prior cycle, activity/session or reset-credit count enters compliance.

## DEC-1817 — STALE display is conservative

The pure evaluator may describe the factual coordinates of an observation, but Current Details MUST NOT label a STALE observation as current Plan compliance.

PlanPanel shows a stale/unavailable message instead.

Alerts ignore STALE.

## DEC-1818 — Existing behavior fixes are separated from Plan evolution

Existing contract repairs are tracked in `COHERENCE-BASELINE.md` and remain traceable to their historical REQs/ACs.

They do not become new Plan requirements merely because v1.8 exposed them.

## Complexity accepted

1. One neutral quantities module.
2. One pure Plan application module.
3. One small in-memory Plan alert service/tracker.
4. Settings schema v3 inside the existing repository.
5. One typed checkpoint editor extension to existing Settings.
6. One PlanPanel in existing Current Details.
7. One ADR for schema compatibility.

## Complexity explicitly rejected/deferred

- second settings repository;
- Plan SQLite;
- Plan Event Store;
- Plan cache/revision;
- Plan background executor;
- Plan scheduler;
- generic notification rules;
- predictive model;
- Context/History dependency;
- automatic redeem;
- global Settings runtime/DI rewrite;
- global taxonomy renaming campaign;
- removal of legacy controllers without a separate reference/migration audit.
