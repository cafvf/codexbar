# CodexBar v1.8 — Product Decisions

Status: frozen for requirements drafting  
Theme: Plan

These decisions define v1.8 product semantics. Changing them requires an explicit
specification amendment before implementation.

## DEC-1801 — Current and explicit settings are the only Plan authorities

Decision: ACCEPTED

Plan evaluation uses authoritative Current facts plus explicit user configuration.

History, Historical Context, reset ledger, prior-cycle behavior and inferred usage
rate are not Plan inputs.

## DEC-1802 — Existing reserve remains the single reserve authority

Decision: ACCEPTED

The existing per-`UsageWindowId` `UsageReservePolicy` remains canonical.

v1.8 must not create an independently configurable second `reserve_floor`.

Budget keeps its existing reserve/headroom contract.

## DEC-1803 — Plan checkpoints are keyed only by UsageWindowId

Decision: ACCEPTED

Checkpoint policy is associated with dynamic `UsageWindowId`.

Policy must not be inherited by:

- human label;
- display order;
- guessed window duration;
- fixed "5h" / "weekly" aliases.

Unknown/new window IDs do not inherit another window's Plan policy.

## DEC-1804 — Checkpoints use time-to-reset coordinates

Decision: ACCEPTED

A checkpoint is defined by:

- a time-to-reset duration; and
- a minimum remaining fraction.

Checkpoint policy does not use absolute timestamps or time-since-cycle-start as its
canonical coordinate.

## DEC-1805 — Checkpoint evaluation is a step function

Decision: ACCEPTED

A checkpoint at threshold `t_i` is reached when current factual time-to-reset `t`
satisfies:

`t <= t_i`

The active checkpoint is the reached checkpoint with the smallest `t_i`.

The active floor remains in force until a later checkpoint is reached.

No interpolation is performed.

## DEC-1806 — Effective floor is the maximum applicable explicit floor

Decision: ACCEPTED

When both reserve and active checkpoint floor exist:

`effective_floor = max(reserve, active_checkpoint_floor)`

When only one exists, that component is the effective floor.

Checkpoint policy may not silently weaken the existing reserve.

## DEC-1807 — Plan margin is signed

Decision: ACCEPTED

For remaining `R` and effective floor `F`:

`margin = R - F`

Plan must preserve negative margin below policy rather than clipping it to zero.

Existing Budget headroom semantics remain unchanged.

## DEC-1808 — Core Plan outcomes distinguish above, equality and below

Decision: ACCEPTED

When an effective floor exists, core semantic outcomes are:

- above Plan when `R > F`;
- at Plan when `R == F`;
- below Plan when `R < F`.

`NO_PLAN` means no reserve and no checkpoint policy are configured for that
`UsageWindowId`.

A configured checkpoint policy whose first checkpoint has not yet become active is
not `NO_PLAN`. A configured policy whose checkpoint assessment is unavailable is
also not `NO_PLAN`.

Equality is compliant.

Final Python enum names and final UI wording for pending/unavailable states may be
chosen during requirements and architecture work without changing this semantic
partition.

## DEC-1809 — Missing reset time causes partial capability degradation

Decision: ACCEPTED

When factual `resets_at` is unavailable:

- checkpoint selection is unavailable;
- reserve assessment remains valid if reserve exists;
- CodexBar does not infer reset timing from identifiers, labels, History or prior
  cycles.

"Policy exists but checkpoint cannot currently be evaluated" must remain distinct
from "no policy configured".

## DEC-1810 — Duplicate checkpoint times are invalid; non-monotonic floors are valid

Decision: ACCEPTED

Within one window policy, checkpoint time-to-reset values must be unique.

Entry order has no semantic meaning and may be normalized.

Checkpoint minimum floors are not required to be monotonic as reset approaches.
Plan evaluates explicit policy compliance, not policy feasibility.

## DEC-1811 — Canonical checkpoint duration is integer seconds

Decision: ACCEPTED

Time-to-reset thresholds use non-negative integer seconds as the canonical
domain/persistence unit.

UI may render human-friendly hours/days.

Floating-point duration is not the canonical policy representation.

## DEC-1812 — Settings evolution is additive and backward-compatible

Decision: ACCEPTED

Checkpoint policy belongs to canonical application settings.

Existing schema-v2 `usage_reserves` meaning must not change.

A new persistent checkpoint field requires a settings schema-version increment.

Valid prior settings load without checkpoint policy and are not automatically
rewritten merely by being read.

Exact new JSON field shape is deferred to the settings requirement.

## DEC-1813 — Stale observations are presentation evidence, not transition authority

Decision: ACCEPTED

A stale snapshot may be displayed with explicit freshness and a deterministic
comparison derived from its last-known values.

Stale data must not generate a new Plan transition notification or side effect.

## DEC-1814 — v1.8 Plan notification is only transition into below-Plan

Decision: ACCEPTED

The only new Plan alert behavior in the core candidate scope is factual transition
from a non-below state into below-Plan.

Repeated below-Plan observations are silent.

Leaving below-Plan rearms the tracker.

No generic notification rules engine is introduced.

## DEC-1815 — Historical Context cannot influence Plan

Decision: ACCEPTED

Historical Context remains descriptive.

Its cycle selection, empirical bands, coverage, quantiles and any future Explore
surface cannot change:

- Plan floor;
- Plan margin;
- Plan status;
- Plan notification transitions.

## DEC-1816 — Plan does not predict future compliance

Decision: ACCEPTED

Plan evaluates the floor that is applicable **now**.

CodexBar must not label Current as "on Plan" merely because it is above a future
checkpoint floor when that checkpoint has not yet become active.

No consumption forecast, predicted checkpoint state or time-to-exhaustion estimate
is introduced.

## DEC-1817 — Reset credits do not enter Plan-status calculation

Decision: ACCEPTED

Reset-credit inventory, expiry and ledger events do not alter Plan status.

Redeem remains explicit, manual, durable and idempotent.

Automatic redeem remains prohibited.

Reset-credit expiry/count-change notifications are not core Plan semantics.

## DEC-1818 — Plan remains explainable

Decision: ACCEPTED

A user-visible Plan assessment must be able to explain the inputs that determined
the result, including as applicable:

- Current remaining;
- reserve;
- active checkpoint;
- checkpoint floor;
- effective floor;
- signed margin;
- freshness/capability limitations.

History must not be required to explain a Plan result.

## DEC-1819 — Budget and Control remain independent from Plan

Decision: ACCEPTED

Plan may consume the canonical reserve semantic, but Budget and Control do not
depend on Plan.

Plan must not mutate reserve, alter Control opportunity decisions or trigger
redeem.

## DEC-1820 — No Plan-specific historical persistence is authorized

Decision: ACCEPTED

v1.8 does not introduce a Plan Event Store, Plan history database or new historical
analytics store.

Settings persistence is sufficient for explicit policy.

Any future persistence of Plan evaluations requires a separate product decision.
